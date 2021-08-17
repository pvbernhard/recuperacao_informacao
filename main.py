import funcoes_recuperacao as sri
import zipfile

BASE_FOLDER = 'league_of_legends'
REPRESENTACAO_FOLDER = 'representacao'

arquivos_url = 'https://raw.githubusercontent.com/pvbernhard/recuperacao_informacao/master/league_of_legends'

texto_busca = 'teste'


with st.form(key='form'):

  uploaded_files = st.file_uploader("Arquivos", accept_multiple_files=True)
  for uploaded_file in uploaded_files:
    with zipfile.ZipFile(uploaded_file.name,"r") as zip_ref:
      zip_ref.extractall()

  text_input = st.text_input(label='Sua pesquisa')
  submit_button = st.form_submit_button(label='Pesquisar')

  if submit_button:
    st.write(f'teste')


# sri.pesquisa(texto_busca, REPRESENTACAO_FOLDER, BASE_FOLDER, arquivos_url)