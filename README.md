# 🚚 Emplacamentos De Nigris - App Streamlit

Este é um aplicativo web desenvolvido em Streamlit para consulta e análise de dados de emplacamentos de caminhões da De Nigris. Ele permite buscar clientes, visualizar histórico, analisar tendências e prever próximas compras, além de permitir a atualização dos dados através do upload de novas planilhas Excel.

## ✅ Funcionalidades

*   **Busca Inteligente:** Encontre clientes por Nome ou CNPJ.
*   **Visualização Detalhada:** Acesse informações completas do cliente, incluindo total emplacado, último emplacamento e preferências (modelo, marca, concessionária, segmento).
*   **Histórico Interativo:** Gráfico de barras mostrando o histórico mensal de emplacamentos do cliente.
*   **Previsão de Compra:** Estimativa do mês e ano da próxima compra provável, baseada no histórico.
*   **Insights de Vendas:** Frases de apoio geradas automaticamente com base no perfil e histórico do cliente.
*   **Filtros Gerais:** Filtre a base de dados por Marca ou Segmento (opcional, na barra lateral).
*   **Upload de Dados:** Atualize a base de dados facilmente carregando um novo arquivo Excel (.xlsx) pela interface.
*   **Design Moderno:** Interface limpa, responsiva e com a identidade visual da De Nigris.

## 🚀 Como Publicar no Streamlit Cloud (Link Permanente e Gratuito)

Siga estes passos para colocar seu aplicativo online com um link permanente que qualquer pessoa pode acessar:

**Passo 1: Ter uma Conta no GitHub**

*   Se você ainda não tem uma conta no GitHub, crie uma gratuitamente em [https://github.com/join](https://github.com/join).

**Passo 2: Criar um Repositório no GitHub**

1.  Faça login na sua conta do GitHub.
2.  Clique no botão "+" no canto superior direito e selecione "New repository".
3.  Dê um nome ao seu repositório (ex: `emplacamento-app-denigris`).
4.  Escolha a opção "Public" (Importante: precisa ser público para o Streamlit Cloud gratuito).
5.  **Não** marque nenhuma das opções como "Add a README file", "Add .gitignore" ou "Choose a license" por enquanto. Vamos adicionar os arquivos manualmente.
6.  Clique em "Create repository".

**Passo 3: Fazer Upload dos Arquivos do Projeto**

1.  Na página do seu repositório recém-criado, clique no link "uploading an existing file".
2.  Descompacte o arquivo `.zip` que eu te enviei (`emplacamento_streamlit_final.zip`).
3.  Arraste os seguintes arquivos e a pasta `data` para a área de upload do GitHub:
    *   `app.py`
    *   `requirements.txt`
    *   `README.md` (este arquivo)
    *   A pasta `data` (contendo o arquivo Excel e os logos)
4.  Após arrastar os arquivos, espere o upload completar.
5.  No campo "Commit changes" (Confirmar alterações), digite uma mensagem (ex: "Versão inicial do app de emplacamentos").
6.  Clique no botão "Commit changes".

**Passo 4: Criar Conta e Implantar no Streamlit Cloud**

1.  Acesse [https://streamlit.io/cloud](https://streamlit.io/cloud).
2.  Clique em "Sign in with GitHub" e autorize o Streamlit a acessar sua conta do GitHub.
3.  Após o login, você será direcionado ao seu workspace. Clique no botão "New app" (ou "Deploy an app").
4.  Selecione o repositório que você acabou de criar (ex: `emplacamento-app-denigris`).
5.  Verifique se as configurações estão corretas:
    *   **Repository:** Seu repositório (ex: `seu-usuario/emplacamento-app-denigris`)
    *   **Branch:** `main` (ou `master`, dependendo do nome padrão do seu GitHub)
    *   **Main file path:** `app.py`
6.  Clique em "Deploy!".

**Passo 5: Aguarde e Acesse!**

*   O Streamlit vai instalar as dependências e iniciar seu aplicativo. Isso pode levar alguns minutos na primeira vez.
*   Assim que terminar, seu aplicativo estará online com um link permanente parecido com `https://seu-usuario-emplacamento-app-denigris.streamlit.app`.
*   **Guarde este link!** Ele é permanente e você pode compartilhá-lo com quem quiser.

## 🔄 Como Atualizar os Dados (Planilha Excel)

Você tem duas opções:

1.  **Pela Interface do App:**
    *   Acesse o link permanente do seu aplicativo.
    *   Na barra lateral esquerda, clique em "Browse files" na seção "Atualizar Dados".
    *   Selecione o novo arquivo Excel (.xlsx) do seu computador.
    *   O aplicativo usará automaticamente os dados do arquivo carregado para as próximas consultas.
    *   **Importante:** O arquivo carregado só fica ativo enquanto você usa o app. Se o app reiniciar (por inatividade ou atualização), ele voltará a usar o arquivo padrão do GitHub.

2.  **Pelo GitHub (Atualização Permanente):**
    *   Vá para o seu repositório no GitHub.
    *   Navegue até a pasta `data`.
    *   Clique no arquivo Excel existente (ex: `EMPLACAMENTO ANUAL - CAMINHÕES.xlsx`).
    *   Clique no ícone de lápis ("Edit this file") ou nos três pontinhos e "Upload files" para substituir.
    *   Se estiver substituindo, faça o upload do novo arquivo Excel com o **mesmo nome** do antigo.
    *   Faça o "Commit changes".
    *   O Streamlit Cloud detectará a mudança e atualizará seu aplicativo automaticamente em alguns minutos, usando o novo arquivo como padrão.

---

Desenvolvido com ❤️ usando Streamlit e Manus IA.

