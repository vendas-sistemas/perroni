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
        com critérios: produtividade, menor retrabalho, menor ociosidade
        """
        etapas = Etapa.objects.filter(
            numero_etapa=numero_etapa,
            concluida=True,
            data_inicio__isnull=False,
            data_termino__isnull=False
        )
        
        pedreiros_performance = defaultdict(lambda: {
            'dias_list': [],
            'total_retrabalho': 0,
            'total_ociosidade': 0,
            'total_apontamentos': 0,
            'total_horas': Decimal('0.0'),
        })
        
        for etapa in etapas:
            dias = (etapa.data_termino - etapa.data_inicio).days
            
            apontamentos = ApontamentoFuncionario.objects.filter(
                obra=etapa.obra,
                etapa=etapa,
                data__gte=etapa.data_inicio,
                data__lte=etapa.data_termino,
                funcionario__funcao='pedreiro'
            ).select_related('funcionario')
            
            # Fallback: also consider apontamentos without etapa link
            if not apontamentos.exists():
                apontamentos = ApontamentoFuncionario.objects.filter(
                    obra=etapa.obra,
                    data__gte=etapa.data_inicio,
                    data__lte=etapa.data_termino,
                    funcionario__funcao='pedreiro'
                ).select_related('funcionario')
            
            for ap in apontamentos:
                perf = pedreiros_performance[ap.funcionario]
                perf['dias_list'].append(dias)
                perf['total_apontamentos'] += 1
                perf['total_horas'] += ap.horas_trabalhadas or Decimal('0.0')
                if ap.houve_retrabalho:
                    perf['total_retrabalho'] += 1
                if ap.houve_ociosidade:
                    perf['total_ociosidade'] += 1
        
        ranking_data = []
        for pedreiro, perf in pedreiros_performance.items():
            if not perf['dias_list']:
                continue
            media_dias = sum(perf['dias_list']) / len(perf['dias_list'])
            taxa_retrabalho = (perf['total_retrabalho'] / perf['total_apontamentos'] * 100) if perf['total_apontamentos'] > 0 else 0
            taxa_ociosidade = (perf['total_ociosidade'] / perf['total_apontamentos'] * 100) if perf['total_apontamentos'] > 0 else 0
            
            # Score: lower is better (media_dias * (1 + taxa_retrabalho/100) * (1 + taxa_ociosidade/100))
            score = media_dias * (1 + taxa_retrabalho / 100) * (1 + taxa_ociosidade / 100)
            
            ranking_data.append({
                'pedreiro': pedreiro,
                'media_dias': round(media_dias, 2),
                'total_obras': len(perf['dias_list']),
                'total_horas': perf['total_horas'],
                'taxa_retrabalho': round(taxa_retrabalho, 1),
                'taxa_ociosidade': round(taxa_ociosidade, 1),
                'score': round(score, 2),
            })
        
        ranking_data.sort(key=lambda x: x['score'])
        
        return {
            'melhores': ranking_data[:top],
            'piores': ranking_data[-bottom:] if len(ranking_data) > bottom else []
        }
    
    @staticmethod
    def media_dias_por_etapa(clima=None, equipe_ids=None, data_inicio=None, data_fim=None):
        """
        Calcula a média de dias para execução de cada etapa
        com filtros opcionais de clima, equipe e período
        """
        resultado = {}
        
        for numero in range(1, 6):
            etapas = Etapa.objects.filter(
                numero_etapa=numero,
                concluida=True,
                data_inicio__isnull=False,
                data_termino__isnull=False
            )
            
            if data_inicio:
                etapas = etapas.filter(data_inicio__gte=data_inicio)
            if data_fim:
                etapas = etapas.filter(data_termino__lte=data_fim)
            
            total_dias = 0
            count = 0
            
            for etapa in etapas:
                # Apply clima filter
                if clima:
                    has_clima = ApontamentoFuncionario.objects.filter(
                        obra=etapa.obra,
                        data__gte=etapa.data_inicio,
                        data__lte=etapa.data_termino,
                        clima=clima
                    ).exists()
                    if not has_clima:
                        continue
                
                # Apply equipe filter
                if equipe_ids:
                    has_equipe = ApontamentoFuncionario.objects.filter(
                        obra=etapa.obra,
                        data__gte=etapa.data_inicio,
                        data__lte=etapa.data_termino,
                        funcionario_id__in=equipe_ids
                    ).exists()
                    if not has_equipe:
                        continue
                
                dias = (etapa.data_termino - etapa.data_inicio).days
                total_dias += dias
                count += 1
            
            media = total_dias / count if count > 0 else 0
            resultado[numero] = {
                'media': round(media, 2),
                'total_etapas': count,
            }
        
        return resultado
    
    @staticmethod
    def rendimento_individual_pedreiro(pedreiro_id):
        """
        Calcula o rendimento individual de um pedreiro com métricas avançadas
        """
        try:
            pedreiro = Funcionario.objects.get(id=pedreiro_id)
        except Funcionario.DoesNotExist:
            return None
        
        apontamentos = ApontamentoFuncionario.objects.filter(
            funcionario=pedreiro
        ).select_related('obra', 'etapa')
        
        total_dias_trabalhados = apontamentos.count()
        obras_trabalhadas = apontamentos.values('obra').distinct().count()
        total_horas = apontamentos.aggregate(t=Sum('horas_trabalhadas'))['t'] or Decimal('0.0')
        
        # Taxa de retrabalho e ociosidade globais
        dias_retrabalho = apontamentos.filter(houve_retrabalho=True).count()
        dias_ociosidade = apontamentos.filter(houve_ociosidade=True).count()
        taxa_retrabalho = (dias_retrabalho / total_dias_trabalhados * 100) if total_dias_trabalhados > 0 else 0
        taxa_ociosidade = (dias_ociosidade / total_dias_trabalhados * 100) if total_dias_trabalhados > 0 else 0
        
        # Performance por etapa
        performance_etapas = {}
        for numero_etapa in range(1, 6):
            etapas = Etapa.objects.filter(
                concluida=True,
                numero_etapa=numero_etapa,
                data_inicio__isnull=False,
                data_termino__isnull=False
            )
            
            dias_totais = []
            horas_etapa = Decimal('0.0')
            retrabalho_etapa = 0
            ociosidade_etapa = 0
            total_ap_etapa = 0
            
            for etapa in etapas:
                aps_etapa = apontamentos.filter(
                    obra=etapa.obra,
                    data__gte=etapa.data_inicio,
                    data__lte=etapa.data_termino
                )
                
                if aps_etapa.exists():
                    dias = (etapa.data_termino - etapa.data_inicio).days
                    dias_totais.append(dias)
                    for ap in aps_etapa:
                        horas_etapa += ap.horas_trabalhadas or Decimal('0.0')
                        total_ap_etapa += 1
                        if ap.houve_retrabalho:
                            retrabalho_etapa += 1
                        if ap.houve_ociosidade:
                            ociosidade_etapa += 1
            
            if dias_totais:
                performance_etapas[numero_etapa] = {
                    'media_dias': round(sum(dias_totais) / len(dias_totais), 2),
                    'total_execucoes': len(dias_totais),
                    'total_horas': horas_etapa,
                    'taxa_retrabalho': round(retrabalho_etapa / total_ap_etapa * 100 if total_ap_etapa else 0, 1),
                    'taxa_ociosidade': round(ociosidade_etapa / total_ap_etapa * 100 if total_ap_etapa else 0, 1),
                }
        
        # Produtividade: calcular m²/dia para reboco, blocos/dia para parede
        produtividade = AnalyticsService._calcular_produtividade_pedreiro(pedreiro, apontamentos)
        
        return {
            'pedreiro': pedreiro,
            'total_dias_trabalhados': total_dias_trabalhados,
            'total_horas': total_horas,
            'obras_trabalhadas': obras_trabalhadas,
            'taxa_retrabalho': round(taxa_retrabalho, 1),
            'taxa_ociosidade': round(taxa_ociosidade, 1),
            'performance_por_etapa': performance_etapas,
            'produtividade': produtividade,
        }
    
    @staticmethod
    def _calcular_produtividade_pedreiro(pedreiro, apontamentos):
        """Calcula produtividade em unidades específicas (m²/dia, blocos/dia)"""
        produtividade = {}
        
        # Reboco externo: m²/dia
        from apps.obras.models import Etapa3Instalacoes
        etapas3 = Etapa.objects.filter(
            numero_etapa=3,
            concluida=True,
            data_inicio__isnull=False,
            data_termino__isnull=False
        )
        
        total_m2_reboco = Decimal('0.0')
        total_dias_reboco = 0
        
        for etapa in etapas3:
            aps = apontamentos.filter(
                obra=etapa.obra,
                data__gte=etapa.data_inicio,
                data__lte=etapa.data_termino
            )
            if aps.exists():
                try:
                    inst = etapa.instalacoes
                    total_workers = ApontamentoFuncionario.objects.filter(
                        obra=etapa.obra,
                        data__gte=etapa.data_inicio,
                        data__lte=etapa.data_termino,
                        funcionario__funcao='pedreiro'
                    ).values('funcionario').distinct().count()
                    if total_workers > 0:
                        m2_per_worker = (inst.reboco_externo_m2 + inst.reboco_interno_m2) / total_workers
                        dias_trabalhados = aps.count()
                        total_m2_reboco += m2_per_worker
                        total_dias_reboco += dias_trabalhados
                except Exception:
                    pass
        
        if total_dias_reboco > 0:
            produtividade['reboco_m2_dia'] = round(float(total_m2_reboco / total_dias_reboco), 2)
        
        # Blocos/dia (Etapa 1 - parede 7 fiadas)
        from apps.obras.models import Etapa1Fundacao
        etapas1 = Etapa.objects.filter(
            numero_etapa=1,
            concluida=True,
            data_inicio__isnull=False,
            data_termino__isnull=False
        )
        
        total_blocos = 0
        total_dias_blocos = 0
        
        for etapa in etapas1:
            aps = apontamentos.filter(
                obra=etapa.obra,
                data__gte=etapa.data_inicio,
                data__lte=etapa.data_termino
            )
            if aps.exists():
                try:
                    fund = etapa.fundacao
                    total_workers = ApontamentoFuncionario.objects.filter(
                        obra=etapa.obra,
                        data__gte=etapa.data_inicio,
                        data__lte=etapa.data_termino,
                        funcionario__funcao='pedreiro'
                    ).values('funcionario').distinct().count()
                    if total_workers > 0:
                        blocos_per_worker = fund.parede_7fiadas_blocos / total_workers
                        dias_trabalhados = aps.count()
                        total_blocos += blocos_per_worker
                        total_dias_blocos += dias_trabalhados
                except Exception:
                    pass
        
        if total_dias_blocos > 0:
            produtividade['blocos_dia'] = round(total_blocos / total_dias_blocos, 2)
        
        return produtividade
    
    @staticmethod
    def custo_mao_obra_por_obra(obra_id, data_inicio=None, data_fim=None):
        """
        Calcula o custo de mão de obra de uma obra com detalhes por etapa
        """
        try:
            obra = Obra.objects.get(id=obra_id)
        except Obra.DoesNotExist:
            return None
        
        apontamentos = ApontamentoFuncionario.objects.filter(obra=obra)
        
        if data_inicio:
            apontamentos = apontamentos.filter(data__gte=data_inicio)
        if data_fim:
            apontamentos = apontamentos.filter(data__lte=data_fim)
        
        total_geral = apontamentos.aggregate(
            total=Sum('valor_diaria'),
            dias=Count('id'),
            horas=Sum('horas_trabalhadas'),
        )
        
        # Por funcionário
        por_funcionario = apontamentos.values(
            'funcionario__nome_completo',
            'funcionario__funcao'
        ).annotate(
            total=Sum('valor_diaria'),
            dias=Count('id'),
            horas=Sum('horas_trabalhadas'),
            retrabalhos=Count('id', filter=Q(houve_retrabalho=True)),
            ociosidades=Count('id', filter=Q(houve_ociosidade=True)),
        ).order_by('-total')
        
        # Por tipo de função
        por_funcao = apontamentos.values(
            'funcionario__funcao'
        ).annotate(
            total=Sum('valor_diaria'),
            dias=Count('id'),
            horas=Sum('horas_trabalhadas'),
        )
        
        # Por etapa
        por_etapa = apontamentos.values(
            'etapa__numero_etapa'
        ).annotate(
            total=Sum('valor_diaria'),
            dias=Count('id'),
            horas=Sum('horas_trabalhadas'),
        ).order_by('etapa__numero_etapa')
        
        return {
            'obra': obra,
            'total_geral': total_geral['total'] or Decimal('0.00'),
            'total_dias': total_geral['dias'] or 0,
            'total_horas': total_geral['horas'] or Decimal('0.0'),
            'por_funcionario': list(por_funcionario),
            'por_funcao': list(por_funcao),
            'por_etapa': list(por_etapa),
        }
    
    @staticmethod
    def historico_funcionario_semanal(funcionario_id, semanas=4):
        """
        Retorna histórico de trabalho de um funcionário nas últimas semanas
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
        ).select_related('obra', 'etapa').order_by('-data')
        
        semanas_dict = defaultdict(list)
        
        for apontamento in apontamentos:
            semana = apontamento.data.isocalendar()[1]
            ano = apontamento.data.year
            chave = f"{ano}-W{semana}"
            
            semanas_dict[chave].append({
                'data': apontamento.data,
                'obra': apontamento.obra.nome,
                'etapa': str(apontamento.etapa) if apontamento.etapa else None,
                'horas': apontamento.horas_trabalhadas,
                'valor': apontamento.valor_diaria,
                'clima': apontamento.clima,
                'ociosidade': apontamento.houve_ociosidade,
                'retrabalho': apontamento.houve_retrabalho,
            })
        
        resultado = []
        for chave, apontamentos_semana in sorted(semanas_dict.items(), reverse=True):
            total_semana = sum(a['valor'] for a in apontamentos_semana)
            total_horas = sum(a['horas'] for a in apontamentos_semana)
            ociosidades = sum(1 for a in apontamentos_semana if a['ociosidade'])
            retrabalhos = sum(1 for a in apontamentos_semana if a['retrabalho'])
            
            resultado.append({
                'semana': chave,
                'dias_trabalhados': len(apontamentos_semana),
                'total_horas': total_horas,
                'total_valor': total_semana,
                'ociosidades': ociosidades,
                'retrabalhos': retrabalhos,
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
        """
        hoje = datetime.now().date()
        inicio_mes = hoje.replace(day=1)
        
        total_obras = Obra.objects.filter(ativo=True).count()
        obras_em_andamento = Obra.objects.filter(
            status='em_andamento',
            ativo=True
        ).count()
        
        total_funcionarios = Funcionario.objects.filter(ativo=True).count()
        pedreiros_ativos = Funcionario.objects.filter(
            funcao='pedreiro',
            ativo=True
        ).count()
        
        custo_mes = ApontamentoFuncionario.objects.filter(
            data__gte=inicio_mes
        ).aggregate(total=Sum('valor_diaria'))['total'] or Decimal('0.00')
        
        horas_mes = ApontamentoFuncionario.objects.filter(
            data__gte=inicio_mes
        ).aggregate(total=Sum('horas_trabalhadas'))['total'] or Decimal('0.0')
        
        fiscalizacoes_mes = RegistroFiscalizacao.objects.filter(
            data_fiscalizacao__gte=inicio_mes
        ).count()
        
        # Ocorrências do mês
        apontamentos_mes = ApontamentoFuncionario.objects.filter(data__gte=inicio_mes)
        ociosidades_mes = apontamentos_mes.filter(houve_ociosidade=True).count()
        retrabalhos_mes = apontamentos_mes.filter(houve_retrabalho=True).count()
        
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
                'custo_mes': custo_mes,
                'horas_mes': horas_mes,
            },
            'fiscalizacoes': {
                'total_mes': fiscalizacoes_mes
            },
            'ocorrencias': {
                'ociosidades_mes': ociosidades_mes,
                'retrabalhos_mes': retrabalhos_mes,
            }
        }
