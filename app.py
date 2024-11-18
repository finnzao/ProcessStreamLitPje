import pandas as pd
import plotly.express as px
import streamlit as st
import chardet
import re

# Função para determinar se um processo é Meta2
def is_meta2(numero_processo, ano_corte):
    try:
        ano_processo = int(numero_processo.split("-")[1].split(".")[0])
        return ano_processo < ano_corte
    except Exception:
        return False

# Função para detectar a codificação do arquivo
def detect_encoding(uploaded_file):
    raw_data = uploaded_file.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    uploaded_file.seek(0)  # Resetar o ponteiro para o início do arquivo
    return encoding

# Ler a planilha (csv ou xlsx)
def process_data(uploaded_file, ano_corte, delimiters, quotechar):
    try:
        # Verificar o tipo de arquivo com base no nome
        file_extension = uploaded_file.name.split('.')[-1].lower()

        if file_extension == 'xlsx':
            df = pd.read_excel(uploaded_file)
        elif file_extension == 'csv':
            # Detectar a codificação do arquivo
            encoding = detect_encoding(uploaded_file)
            uploaded_file.seek(0)  # Resetar o ponteiro novamente

            # Criar expressão regular para múltiplos delimitadores
            delimiters = delimiters.replace('\\t', '\t')  # Substituir representação da tabulação
            delimiter_regex = '|'.join(map(re.escape, delimiters))

            # Tentar ler o CSV com as configurações fornecidas
            df = pd.read_csv(
                uploaded_file,
                sep=delimiter_regex,
                quotechar=quotechar,
                encoding=encoding,
                engine='python',
                on_bad_lines='skip'
            )
        else:
            raise ValueError("Formato de arquivo não suportado. Use .csv ou .xlsx")
    except Exception as e:
        raise ValueError(f"Erro ao ler o arquivo: {e}")

    # Verificar se as colunas necessárias estão presentes
    required_columns = ['numeroProcesso', 'nomeTarefa']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"A coluna '{col}' é obrigatória no arquivo.")

    # Remover linhas com valores nulos nas colunas necessárias
    df.dropna(subset=required_columns, inplace=True)

    # Adicionar coluna Meta2
    df['Meta2'] = df['numeroProcesso'].apply(lambda x: is_meta2(x, ano_corte))

    return df

# Aplicação Streamlit
def main():
    st.title("Análise de Processos Meta2")

    # Upload do arquivo
    uploaded_file = st.file_uploader("Envie o arquivo CSV ou XLSX", type=["csv", "xlsx"])
    if uploaded_file is not None:
        # Selecionar o ano de corte para Meta2
        ano_corte = st.number_input("Selecione o ano de corte para Meta2:", min_value=1900, max_value=2100, value=2021, step=1)

        # Opções para especificar o delimitador e o caractere de citação
        st.subheader("Configurações do Arquivo CSV")
        delimiters = st.text_input("Delimitadores (pode inserir múltiplos caracteres, por exemplo, '\\t;'):", value='\\t;')
        quotechar = st.text_input("Caractere de citação (padrão é '\"'):", value="'")

        # Processar os dados
        try:
            df = process_data(uploaded_file, ano_corte, delimiters, quotechar)
        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
            return

        # Selecionar se deseja ver todos os processos ou apenas os Meta2
        mostrar_meta2 = st.checkbox("Mostrar apenas processos Meta2", value=True)
        if mostrar_meta2:
            df = df[df['Meta2']]

        # Verificar se há dados após o filtro
        if df.empty:
            st.warning("Nenhum dado disponível para as seleções feitas.")
            return

        # Selecionar os 'nomeTarefa' para exibir
        nome_tarefa_options = df['nomeTarefa'].unique()
        selected_tarefas = st.multiselect("Selecione os Nome da Tarefa para visualizar:", options=nome_tarefa_options, default=nome_tarefa_options)

        # Filtrar o dataframe com as tarefas selecionadas
        df_filtered = df[df['nomeTarefa'].isin(selected_tarefas)]

        # Exibir tabela de dados filtrados
        st.subheader("Dados Filtrados")
        st.write(df_filtered)

        # Contar os processos por 'nomeTarefa'
        task_counts = df_filtered['nomeTarefa'].value_counts()
        total = task_counts.sum()
        percentages = (task_counts / total) * 100

        # Criar DataFrame para a tabela
        table_data = pd.DataFrame({
            'Nome da Tarefa': task_counts.index,
            'Quantidade': task_counts.values,
            'Porcentagem (%)': percentages.round(1).values
        })

        # Exibir tabela
        st.subheader("Quantidade e Porcentagem por Nome da Tarefa")
        st.write(table_data)

        # Verificar se há dados para o gráfico
        if not table_data.empty:
            # Gráfico de Pizza Interativo
            fig = px.pie(
                table_data,
                names='Nome da Tarefa',
                values='Quantidade',
                title='Distribuição de Processos por Nome da Tarefa',
                hole=0.4  # Para transformar em gráfico de rosca
            )
            st.plotly_chart(fig)
        else:
            st.warning("Nenhum dado disponível para gerar o gráfico.")
    else:
        st.info("Por favor, envie um arquivo para iniciar a análise.")

if __name__ == "__main__":
    main()
