"""
Serviços de análise e geração de relatórios
"""
from django.db.models import Count, Sum, Avg, Q, F
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

from apps.obras.models import Obra, Etapa
from apps.funcionarios.models import Funcionario, ApontamentoFuncionario
from apps.fiscalizacao.models import RegistroFiscalizacao


class AnalyticsService:
    """Serviço principal de analytics"""
    
    @staticmethod
    def ranking_pedreiros_por_etapa(numero_etapa, top=3, bottom=3):
        """
        Retorna ranking dos melhores e piores pedreiros em uma etapa específica
        
        Args:
            numero_etapa (int): Número da etapa (1 a 5)
            top (int): Quantidade de melhores a retornar
            bottom (int): Quantidade de piores a retornar
        
        Returns:
            dict: {'melhores': [...], 'piores': [...]}
        """
        # Busca todas as etapas concluídas do número especificado
        etapas = Etapa.objects.filter(
            numero_etapa=numero_etapa,
            concluida=True,
            data_inicio__isnull=False,
            data_termino__isnull=False
        )
        
        # Calcula dias para conclusão de cada etapa
        pedreiros_performance = defaultdict(list)
        
        for etapa in etapas:
            dias = (etapa.data_termino - etapa.data_inicio).days
            
            # Busca pedreiros que trabalharam nesta etapa
            apontamentos = ApontamentoFuncionario.objects.filter(
                obra=etapa.obra,
                data__gte=etapa.data_inicio,
                data__lte=etapa.data_termino,
                funcionario__funcao='pedreiro'
            ).select_related('funcionario')
            
            for apontamento in apontamentos:
                pedreiros_performance[apontamento.funcionario].append(dias)
        
        # Calcula média de dias por pedreiro
        ranking_data = []
        for pedreiro, dias_list in pedreiros_performance.items():
            media_dias = sum(dias_list) / len(dias_list)
            ranking_data.append({
                'pedreiro': pedreiro,
                'media_dias': round(media_dias, 2),
                'total_obras': len(dias_list)
            })
        
        # Ordena por média de dias (menor é melhor)
        ranking_data.sort(key=lambda x: x['media_dias'])
        
        return {
            'melhores': ranking_data[:top],
            'piores': ranking_data[-bottom:] if len(ranking_data) > bottom else []
        }
    
    @staticmethod
    def media_dias_por_etapa():
        """
        Calcula a média de dias para execução de cada etapa
        
        Returns:
            dict: {etapa_numero: media_dias}
        """
        resultado = {}
        
        for numero in range(1, 6):
            etapas = Etapa.objects.filter(
                numero_etapa=numero,
                concluida=True,
                data_inicio__isnull=False,
                data_termino__isnull=False
            )
            
            if etapas.exists():
                total_dias = 0
                count = 0
                
                for etapa in etapas:
                    dias = (etapa.data_termino - etapa.data_inicio).days
                    total_dias += dias
                    count += 1
                
                media = total_dias / count if count > 0 else 0
                resultado[numero] = round(media, 2)
            else:
                resultado[numero] = 0
        
        return resultado
    
    @staticmethod
    def rendimento_individual_pedreiro(pedreiro_id):
        """
        Calcula o rendimento individual de um pedreiro
        
        Args:
            pedreiro_id (int): ID do pedreiro
        
        Returns:
            dict: Estatísticas de rendimento do pedreiro
        """
        try:
            pedreiro = Funcionario.objects.get(id=pedreiro_id, funcao='pedreiro')
        except Funcionario.DoesNotExist:
            return None
        
        # Busca todos os apontamentos
        apontamentos = ApontamentoFuncionario.objects.filter(
            funcionario=pedreiro
        ).select_related('obra')
        
        # Estatísticas gerais
        total_dias_trabalhados = apontamentos.count()
        obras_trabalhadas = apontamentos.values('obra').distinct().count()
        
        # Análise por etapa
        performance_etapas = {}
        for numero_etapa in range(1, 6):
            etapas = Etapa.objects.filter(
                concluida=True,
                numero_etapa=numero_etapa,
                data_inicio__isnull=False,
                data_termino__isnull=False
            )
            
            dias_totais = []
            for etapa in etapas:
                # Verifica se o pedreiro trabalhou nesta etapa
                trabalhou = apontamentos.filter(
                    obra=etapa.obra,
                    data__gte=etapa.data_inicio,
                    data__lte=etapa.data_termino
                ).exists()
                
                if trabalhou:
                    dias = (etapa.data_termino - etapa.data_inicio).days
                    dias_totais.append(dias)
            
            if dias_totais:
                performance_etapas[numero_etapa] = {
                    'media_dias': round(sum(dias_totais) / len(dias_totais), 2),
                    'total_execucoes': len(dias_totais)
                }
        
        return {
            'pedreiro': pedreiro,
            'total_dias_trabalhados': total_dias_trabalhados,
            'obras_trabalhadas': obras_trabalhadas,
            'performance_por_etapa': performance_etapas
        }
    
    @staticmethod
    def custo_mao_obra_por_obra(obra_id, data_inicio=None, data_fim=None):
        """
        Calcula o custo de mão de obra de uma obra
        
        Args:
            obra_id (int): ID da obra
            data_inicio (date): Data inicial para filtro (opcional)
            data_fim (date): Data final para filtro (opcional)
        
        Returns:
            dict: Custos detalhados
        """
        try:
            obra = Obra.objects.get(id=obra_id)
        except Obra.DoesNotExist:
            return None
        
        # Filtra apontamentos
        apontamentos = ApontamentoFuncionario.objects.filter(obra=obra)
        
        if data_inicio:
            apontamentos = apontamentos.filter(data__gte=data_inicio)
        if data_fim:
            apontamentos = apontamentos.filter(data__lte=data_fim)
        
        # Calcula totais
        total_geral = apontamentos.aggregate(
            total=Sum('valor_diaria'),
            dias=Count('id')
        )
        
        # Por funcionário
        por_funcionario = apontamentos.values(
            'funcionario__nome_completo',
            'funcionario__funcao'
        ).annotate(
            total=Sum('valor_diaria'),
            dias=Count('id')
        ).order_by('-total')
        
        # Por tipo de função
        por_funcao = apontamentos.values(
            'funcionario__funcao'
        ).annotate(
            total=Sum('valor_diaria'),
            dias=Count('id')
        )
        
        return {
            'obra': obra,
            'total_geral': total_geral['total'] or Decimal('0.00'),
            'total_dias': total_geral['dias'] or 0,
            'por_funcionario': list(por_funcionario),
            'por_funcao': list(por_funcao)
        }
    
    @staticmethod
    def historico_funcionario_semanal(funcionario_id, semanas=4):
        """
        Retorna histórico de trabalho de um funcionário nas últimas semanas
        
        Args:
            funcionario_id (int): ID do funcionário
            semanas (int): Número de semanas para buscar
        
        Returns:
            list: Histórico semanal
        """
        try:
            funcionario = Funcionario.objects.get(id=funcionario_id)
        except Funcionario.DoesNotExist:
            return None
        
        hoje = datetime.now().date()
        data_inicio = hoje - timedelta(weeks=semanas)
        
        apontamentos = ApontamentoFuncionario.objects.filter(
            funcionario=funcionario,
            data__gte=data_inicio
        ).select_related('obra').order_by('-data')
        
        # Agrupa por semana
        semanas_dict = defaultdict(list)
        
        for apontamento in apontamentos:
            # Calcula número da semana
            semana = apontamento.data.isocalendar()[1]
            ano = apontamento.data.year
            chave = f"{ano}-W{semana}"
            
            semanas_dict[chave].append({
                'data': apontamento.data,
                'obra': apontamento.obra.nome,
                'valor': apontamento.valor_diaria
            })
        
        # Formata resultado
        resultado = []
        for chave, apontamentos_semana in sorted(semanas_dict.items(), reverse=True):
            total_semana = sum(a['valor'] for a in apontamentos_semana)
            resultado.append({
                'semana': chave,
                'dias_trabalhados': len(apontamentos_semana),
                'total_valor': total_semana,
                'detalhes': apontamentos_semana
            })
        
        return {
            'funcionario': funcionario,
            'historico': resultado
        }
    
    @staticmethod
    def dashboard_geral():
        """
        Retorna dados para dashboard geral do sistema
        
        Returns:
            dict: Dados consolidados
        """
        hoje = datetime.now().date()
        inicio_mes = hoje.replace(day=1)
        
        # Obras
        total_obras = Obra.objects.filter(ativo=True).count()
        obras_em_andamento = Obra.objects.filter(
            status='em_andamento',
            ativo=True
        ).count()
        
        # Funcionários
        total_funcionarios = Funcionario.objects.filter(ativo=True).count()
        pedreiros_ativos = Funcionario.objects.filter(
            funcao='pedreiro',
            ativo=True
        ).count()
        
        # Custos do mês
        custo_mes = ApontamentoFuncionario.objects.filter(
            data__gte=inicio_mes
        ).aggregate(total=Sum('valor_diaria'))['total'] or Decimal('0.00')
        
        # Fiscalizações do mês
        fiscalizacoes_mes = RegistroFiscalizacao.objects.filter(
            data_fiscalizacao__gte=inicio_mes
        ).count()
        
        return {
            'obras': {
                'total': total_obras,
                'em_andamento': obras_em_andamento
            },
            'funcionarios': {
                'total': total_funcionarios,
                'pedreiros': pedreiros_ativos
            },
            'financeiro': {
                'custo_mes': custo_mes
            },
            'fiscalizacoes': {
                'total_mes': fiscalizacoes_mes
            }
        }
