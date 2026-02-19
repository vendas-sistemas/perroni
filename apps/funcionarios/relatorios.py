"""
Serviço de relatórios de produção simplificados.

FÓRMULA DE CÁLCULO DE MÉDIA:
---------------------------
Média por dia = Total Produzido ÷ Total de Dias Trabalhados

Exemplo 1 (Blocos):
- Dia 1: 200 blocos
- Dia 2: 100 blocos
- Total: 300 blocos
- Dias: 2
- Média: 300 ÷ 2 = 150 blocos/dia ✅

Exemplo 2 (Percentual):
- Dia 1: 10%
- Dia 2: 2%
- Total: 12%
- Dias: 2
- Média: 12 ÷ 2 = 6%/dia ✅

IMPORTANTE: NÃO usar Django Avg() ou divisão em annotate()!
Sempre calcular em Python: float(total) / int(dias)
"""
from django.db.models import Sum, Count, Min, Q
from decimal import Decimal


class RelatorioProducao:
    """Gera relatórios simplificados de produção"""
    
    @staticmethod
    def ranking_indicador(indicador, data_inicio, data_fim, top=3):
        """
        Gera ranking de um indicador específico baseado na MÉDIA CORRETA.
        
        CORREÇÃO CRÍTICA: Calcula média em Python, não no Django!
        
        Args:
            indicador: 'parede_7fiadas', 'platibanda', 'reboco_externo', etc
            data_inicio: Data inicial
            data_fim: Data final
            top: Quantos mostrar (padrão 3)
        
        Returns:
            Lista com top performers ordenados por média/dia CORRETA
        """
        from apps.funcionarios.models import RegistroProducao
        
        # Buscar produções deste indicador no período
        producoes = RegistroProducao.objects.filter(
            indicador=indicador,
            data__range=[data_inicio, data_fim],
            funcionario__funcao='pedreiro'
        )
        
        # Agrupar por funcionário (SEM calcular média no Django - isso causa o erro!)
        ranking_raw = (
            producoes
            .values('funcionario', 'funcionario__nome_completo')
            .annotate(
                total_valor=Sum('quantidade'),
                total_dias=Count('data', distinct=True)
            )
            .order_by()  # Limpar ordenação default
        )
        
        # ===== CALCULAR MÉDIA CORRETAMENTE EM PYTHON =====
        ranking = []
        for item in ranking_raw:
            total_valor = float(item['total_valor'] or 0)
            total_dias = int(item['total_dias'] or 0)
            
            # Calcular média: Total ÷ Dias
            if total_dias > 0:
                media_dia = total_valor / total_dias
            else:
                media_dia = 0
            
            ranking.append({
                'funcionario': item['funcionario'],
                'funcionario__nome_completo': item['funcionario__nome_completo'],
                'total_valor': round(total_valor, 2),
                'total_dias': total_dias,
                'media_dia': round(media_dia, 2)  # ← MÉDIA CORRETA!
            })
        
        # Ordenar por média (maior primeiro)
        ranking = sorted(ranking, key=lambda x: x['media_dia'], reverse=True)
        
        # Retornar apenas top N
        return ranking[:top]
    
    @staticmethod
    def ranking_conclusao(indicador, data_inicio, data_fim, top=3):
        """
        Gera ranking de velocidade (data de conclusão).
        Quem concluiu PRIMEIRO ganha!
        
        Args:
            indicador: 'laje_conclusao', 'cobertura_conclusao', 'respaldo_conclusao'
            data_inicio: Data inicial
            data_fim: Data final
            top: Quantos mostrar
        
        Returns:
            Lista com os mais rápidos
        """
        from apps.funcionarios.models import RegistroProducao
        
        # Buscar PRIMEIRA data de conclusão de cada funcionário
        producoes = (
            RegistroProducao.objects
            .filter(
                indicador=indicador,
                data__range=[data_inicio, data_fim],
                funcionario__funcao='pedreiro',
                quantidade__gt=0
            )
            .values('funcionario', 'funcionario__nome_completo')
            .annotate(
                data_conclusao_primeira=Min('data')
            )
            .order_by('data_conclusao_primeira')[:top]
        )
        
        # Adicionar posição relativa (dias de diferença do primeiro)
        resultado = list(producoes)
        if resultado:
            primeira_data = resultado[0]['data_conclusao_primeira']
            for item in resultado:
                dias_diferenca = (item['data_conclusao_primeira'] - primeira_data).days
                item['dias_depois'] = dias_diferenca
        
        return resultado
    
    @staticmethod
    def detalhamento_pedreiro(pedreiro, data_inicio, data_fim):
        """
        Gera detalhamento completo de um pedreiro no período.
        
        CORREÇÃO: Calcula médias corretamente em Python!
        
        Returns:
            Dict com todas as informações organizadas
        """
        from apps.funcionarios.models import RegistroProducao, ApontamentoFuncionario
        
        producoes = RegistroProducao.objects.filter(
            funcionario=pedreiro,
            data__range=[data_inicio, data_fim]
        ).select_related('obra')
        
        # Resumo geral
        total_dias = producoes.values('data').distinct().count()
        
        # Obras trabalhadas
        obras = producoes.values('obra__nome').annotate(
            dias=Count('data', distinct=True)
        ).order_by('-dias')
        
        # Agrupar por indicador
        por_indicador = {}
        
        indicadores_info = dict(RegistroProducao._meta.get_field('indicador').choices)
        
        for indicador_code, indicador_nome in indicadores_info.items():
            prods = producoes.filter(indicador=indicador_code)
            
            if not prods.exists():
                continue
            
            # ===== CALCULAR TOTAIS CORRETAMENTE =====
            total_dias_ind = prods.values('data').distinct().count()
            # Somar todos os valores
            total_valor = sum(float(p.quantidade) for p in prods)
            
            # ===== CALCULAR MÉDIA CORRETAMENTE EM PYTHON =====
            if total_dias_ind > 0:
                media_dia = total_valor / total_dias_ind
            else:
                media_dia = 0
            
            # Buscar ranking para saber posição
            etapa = prods.first().etapa if prods.first() else None
            etapa_num = etapa.numero_etapa if etapa else None
            
            # Para indicadores de conclusão (baseados em data)
            if indicador_code.endswith('_conclusao'):
                ranking_pos = RelatorioProducao.ranking_conclusao(
                    indicador_code,
                    data_inicio,
                    data_fim,
                    top=100
                )
                
                posicao = None
                data_conclusao = None
                dias_depois = None
                for idx, item in enumerate(ranking_pos, 1):
                    if item['funcionario'] == pedreiro.id:
                        posicao = idx
                        data_conclusao = item['data_conclusao_primeira']
                        dias_depois = item.get('dias_depois', 0)
                        break
                
                por_indicador[indicador_code] = {
                    'nome': indicador_nome,
                    'etapa': etapa_num,
                    'tipo': 'conclusao',
                    'data_conclusao': data_conclusao,
                    'dias_depois': dias_depois,
                    'posicao': posicao,
                }
            
            # Para indicadores quantitativos
            else:
                ranking_pos = RelatorioProducao.ranking_indicador(
                    indicador_code,
                    data_inicio,
                    data_fim,
                    top=100
                )
                
                posicao = None
                for idx, item in enumerate(ranking_pos, 1):
                    if item['funcionario'] == pedreiro.id:
                        posicao = idx
                        break
                
                # Detalhes por dia
                detalhes_dia = list(prods.values(
                    'data', 'obra__nome', 'quantidade', 'etapa__numero_etapa'
                ).order_by('data'))
                
                por_indicador[indicador_code] = {
                    'nome': indicador_nome,
                    'etapa': etapa_num,
                    'tipo': 'quantitativo',
                    'total_valor': round(total_valor, 2),
                    'total_dias': total_dias_ind,
                    'media_dia': round(media_dia, 2),  # ← MÉDIA CORRETA!
                    'posicao': posicao,
                    'detalhes_dia': detalhes_dia,
                }
        
        # Calcular horas trabalhadas (via apontamentos)
        apontamentos = ApontamentoFuncionario.objects.filter(
            funcionario=pedreiro,
            data__range=[data_inicio, data_fim]
        )
        total_horas = apontamentos.aggregate(Sum('horas_trabalhadas'))['horas_trabalhadas__sum'] or Decimal('0')
        
        return {
            'pedreiro': pedreiro.nome_completo,
            'periodo': {
                'inicio': data_inicio,
                'fim': data_fim,
            },
            'resumo': {
                'total_dias': total_dias,
                'total_horas': float(total_horas),
                'total_obras': len(obras),
            },
            'obras': list(obras),
            'por_indicador': por_indicador,
        }
    
    @staticmethod
    def ranking_geral(data_inicio, data_fim, top=3):
        """
        Gera ranking completo de todos os indicadores.
        
        Returns:
            Dict organizado por etapas e indicadores
        """
        # Indicadores quantitativos
        indicadores_quant = [
            ('alicerce_percentual', 1, 'Levantar Alicerce (%)'),
            ('parede_7fiadas', 1, 'Parede 7 Fiadas (blocos)'),
            ('platibanda', 2, 'Platibanda (blocos)'),
            ('reboco_externo', 3, 'Reboco Externo (m²)'),
            ('reboco_interno', 3, 'Reboco Interno (m²)'),
        ]
        
        # Indicadores de conclusão
        indicadores_conclusao = [
            ('respaldo_conclusao', 1, '8 Fiadas até Respaldo'),
            ('laje_conclusao', 2, 'Montagem da Laje'),
            ('cobertura_conclusao', 2, 'Cobertura Completa'),
        ]
        
        resultado = {
            'etapa_1': {'nome': 'Etapa 1 - Fundação', 'indicadores': {}},
            'etapa_2': {'nome': 'Etapa 2 - Estrutura', 'indicadores': {}},
            'etapa_3': {'nome': 'Etapa 3 - Instalações', 'indicadores': {}},
        }
        
        # Processar indicadores quantitativos
        for indicador, etapa, nome in indicadores_quant:
            ranking = RelatorioProducao.ranking_indicador(indicador, data_inicio, data_fim, top)
            resultado[f'etapa_{etapa}']['indicadores'][indicador] = {
                'nome': nome,
                'tipo': 'quantitativo',
                'ranking': ranking,
            }
        
        # Processar indicadores de conclusão
        for indicador, etapa, nome in indicadores_conclusao:
            ranking = RelatorioProducao.ranking_conclusao(indicador, data_inicio, data_fim, top)
            resultado[f'etapa_{etapa}']['indicadores'][indicador] = {
                'nome': nome,
                'tipo': 'conclusao',
                'ranking': ranking,
            }
        
        return resultado
