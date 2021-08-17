import streamlit as st

from typing import List, Dict, Any, Optional, Tuple, Union

import os
import pandas as pd

import nltk


nltk.download('stopwords')
nltk.download('punkt')


"""
REPRESENTAÇÃO
"""

def gera_tokens(texto: str = '',
                palavras: List[str] = None, 
                linguagem: str = 'portuguese',
                no_stemming: bool = False) -> Optional[List[str]]:
  """
  Gera tokens baseado em um texto.
  """
  from nltk.corpus import stopwords
  from nltk.tokenize import word_tokenize
  from nltk.stem.snowball import SnowballStemmer
  from unidecode import unidecode

  tokens = None

  if len(texto) > 0:
    # gera stop words
    stop_words = set(stopwords.words(linguagem))

    # tokeniza o texto
    tokens = word_tokenize(texto)

    # remove palavras com tamanho < 3
    # remove pontuações (strip)
    # transforma em caixa baixa (lower)
    tokens = [t.lower() for t in tokens if len(t) >= 3 and t.strip()]

    # remove stop words
    tokens = [t for t in tokens if not t.lower() in stop_words]

    # stemming
    if not no_stemming:
      stemmer = SnowballStemmer(language=linguagem)
      tokens = [stemmer.stem(t) for t in tokens]

    # remove acentos (unidecode)
    tokens = [unidecode(t) for t in tokens]
  elif palavras:
    tokens = []

    for idx, palavra in enumerate(palavras):
      token = gera_tokens(texto=palavra,
                          no_stemming=no_stemming)
      tokens.extend(token)

  return tokens


def get_representacao(arquivo_caminho: str,
                      no_stemming: bool = False) -> Dict[str, Dict[str, int]]:
  """
  Gera a representação do arquivo com a frequência de cada token.

  Exemplo retorno:
  {
    "token": {
      "relevancia": 10,
      "frequencia": 7
    }, ...
  }
  """
  from collections import Counter

  f = open(arquivo_caminho, 'r')
  linhas = f.readlines()
  f.close()

  # remove url das imagens
  linhas.pop(22)  # habilidades
  linhas.pop(18)
  linhas.pop(14)
  linhas.pop(10)
  linhas.pop(6)  # passiva
  linhas.pop(2)  # retrato

  texto = '\n'.join(linhas)

  titulo_tokens = gera_tokens(texto=linhas[0],
                              no_stemming=no_stemming)

  tags_tokens = gera_tokens(texto=linhas[1],
                            no_stemming=no_stemming)

  tokens = gera_tokens(texto=texto,
                       no_stemming=no_stemming)

  frequencias = dict(Counter(tokens))

  for chave in frequencias:
    frequencias[chave] = {
        'relevancia': 1,
        'frequencia': frequencias[chave]
    }
  
  # relevancias para nome, titulo, e tags
  titulo_relevancia = 10
  tags_relevancia = 5

  for token in titulo_tokens:
    if token in frequencias:
      frequencias.get(token)['relevancia'] = titulo_relevancia
  
  for token in tags_tokens:
    if token in frequencias:
      frequencias.get(token)['relevancia'] = tags_relevancia

  return frequencias


def gera_representacoes(de_caminho: str,
                        para_caminho: str) -> None:
  """
  Gera arquivos de representações com as frequências de cada token.
  """
  import os, json, ntpath
  from glob import glob

  de_caminho = os.path.join(de_caminho, '*.txt')
  
  arquivos = glob(de_caminho)

  for arquivo in arquivos:
    arquivo_nome = ntpath.basename(arquivo)
    arquivo_nome = arquivo_nome.rsplit('.', 1)[0] + '.json'
    representacao = get_representacao(arquivo)
    with open(os.path.join(para_caminho, arquivo_nome), "w") as outfile:
      json.dump(representacao, outfile)
    print(f"{arquivo} processado.")

  print('Arquivos de representação gerados.')

"""
RECUPERACAO
"""

def calcula_idfs(arquivos_pasta: str,
                 tokens: List[str]
                 ) -> Tuple[Dict[str, float], Dict[str, float]]:
  """
  Calcula idf de cada palavra em uma lista em relação a um diretório de jsons.
  """
  from glob import glob
  import os, json

  docs_caminhos = glob(os.path.join(arquivos_pasta, '*.json'))
  n_docs = len(docs_caminhos)
  n_docs_com_termos = [0 for _ in tokens]
  max_freq = {}
  for caminho in docs_caminhos:
    with open(caminho) as arquivo:
      representacao = json.load(arquivo)
      for idx, token in enumerate(tokens):
        if token in representacao:
          n_docs_com_termos[idx] += 1
          if not max_freq.get(token) or \
              representacao.get(token).get('frequencia') > max_freq.get(token):
            max_freq[token] = representacao.get(token).get('frequencia')
  
  idfs = {}
  for idx, n_docs_com_termo in enumerate(n_docs_com_termos):
    if n_docs_com_termo != 0:
      idfs[tokens[idx]] = float(n_docs / n_docs_com_termo)
    else:
      idfs[tokens[idx]] = 0.0
  return idfs, max_freq


def calcula_pesos(representacao: Dict[str, Dict[str, int]],
                  tokens: List[str],
                  idfs: Dict[str, float],
                  max_freq: Dict[str, float]) -> Dict[str, float]:
  """
  Calcula pesos de cada token em um documento. w = freq * idf
  """
  import os, json

  pesos = {}

  for token in tokens:
    if token in representacao:
      frequencia = representacao.get(token).get('frequencia')
      pesos[token] = frequencia * idfs[token]
      # normalizando
      pesos[token] /= max_freq[token] * idfs[token]
    else:
      pesos[token] = 0.0

  return pesos


def calcula_similaridade(representacao: Dict[str, Dict[str, int]],
                         pesos: Dict[str, float],
                         p: int = 3) -> float:
  """
  Calcula similaridade entre doc e busca de acordo com os pesos.
  Fórmula: 1-( (wl1^p(1-w1)^p+wl2^p(1-w2)^p+...) / (wl1^p+wl2^p+...) )^(1/p)
  """
  import math

  somatorio_pesos = 0
  for token in pesos:
    somatorio_pesos += pesos.get(token)
  if somatorio_pesos == 0:
    return float('-inf')
  
  somatorio_numerador = 0.0
  for token in pesos:
    peso_relevancia = 1
    if token in representacao:
      peso_relevancia = representacao.get(token).get('relevancia')
    somatorio_numerador += \
      math.pow(peso_relevancia, p) * math.pow(1.0 - pesos.get(token), p)
  
  somatorio_denominador = 1.0
  for token in pesos:
    peso_relevancia = 1
    if token in representacao:
      peso_relevancia = representacao.get(token).get('relevancia')
    somatorio_denominador += math.pow(peso_relevancia, p)

  return 1 - math.pow(somatorio_numerador / somatorio_denominador, 1 / p)


def calcula_similaridades(pesquisa: str,
                          arquivos_pasta: str,
                          ) -> List[Dict[str,
                                         Union[str, float, Dict[str, float]]]]:
    """
    Calcula similaridade de todos os arquivos com a pesquisa.
    Exemplo retorno:
    [{
        "id": "id",
        "pesos": {
          "termo1": 0.5,
          "termo2": 0.7, ...
        },
        "similaridade": 0.6
    }, ...]
    """
    from glob import glob
    import os, re, json

    # separa a pesquisa por espaços, vírgulas, ou pontos
    # levando em consideração possíveis números reais
    termos_pesquisa = re.split("\s|(?<!\d)[,.](?!\d)", pesquisa)

    tokens = gera_tokens(palavras=termos_pesquisa)

    idfs, max_freq = calcula_idfs(arquivos_pasta=arquivos_pasta,
                                  tokens=tokens)

    docs_caminhos = glob(os.path.join(arquivos_pasta, '*.json'))

    similaridades = []
    for caminho in docs_caminhos:
      with open(caminho) as arquivo:
        similaridade = {}
        representacao = json.load(arquivo)
        similaridade['id'] = os.path.basename(caminho).rsplit('.', 1)[0]
        pesos = calcula_pesos(representacao=representacao,
                               tokens=tokens,
                               idfs=idfs,
                               max_freq=max_freq)
        similaridade['pesos'] = pesos
        similaridade['similaridade'] =\
          calcula_similaridade(representacao=representacao,
                               pesos=pesos)
        similaridades.append(similaridade)

    return similaridades


def resultado(busca: str,
              representacoes_caminho: str
              ) -> List[Dict[str, Any]]:
  """
  Retorna os resultados da busca.
  """
  similaridades = calcula_similaridades(busca, representacoes_caminho)

  return sorted(similaridades,
                key=lambda key: key.get('similaridade'),
                reverse=True)


def mostra_titulo(titulo: Union[str, bool] = False) -> None:

  if not bool(titulo):
    st.write(f'A busca precisa ter 3 ou mais caracteres.')
  else:
    st.write(f'# Pesquisa: "{titulo}"')


def mostra_resultados(resultados: List[Dict[str, Any]],
                      arquivos_caminho: str,
                      arquivos_url: str) -> None:
  """
  Mostra os resultados na célula.
  """
  import os

  contador = 0
  for resultado in resultados:
    if resultado.get('similaridade') != float('-inf'):
      contador += 1
      id = resultado.get('id')

      f = open(os.path.join(arquivos_caminho, id + '.txt'), 'r')
      linhas = f.readlines()
      f.close()

      retrato = linhas[2]

      st.write(f'##\# {contador} - {linhas[0]}')
      st.image(retrato)

      url = arquivos_url + '/' + id + '.txt'
      
      st.write('Similaridade: ' + resultado.get('similaridade'))
      st.write(url)
      st.write('Resumo: ' + linhas[24])


def pesquisa(busca: str,
             representacao_caminho: str,
             arquivos_caminho: str,
             arquivos_url: str) -> None:
  """
  Faz a pesquisa e mostra os resultados.
  """
  if not bool(busca) or len(busca) < 3:
    mostra_titulo(False)
  else:
    resultado_dict = resultado(busca, representacao_caminho)
    mostra_titulo(busca)
    print()
    mostra_resultados(resultado_dict, arquivos_caminho, arquivos_url)

