import streamlit as st
import funcoes_recuperacao as sri
import zipfile
import os

BASE_FOLDER = 'league_of_legends'
REPRESENTACAO_FOLDER = 'representacao'

arquivos_url = 'https://raw.githubusercontent.com/pvbernhard/recuperacao_informacao/master/league_of_legends'

with st.form(key='form'):
  text_input = st.text_input(label='Sua pesquisa')
  submit_button = st.form_submit_button(label='Pesquisar')

  if submit_button:
    sri.pesquisa(text_input, REPRESENTACAO_FOLDER, BASE_FOLDER, arquivos_url)