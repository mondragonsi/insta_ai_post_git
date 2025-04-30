import streamlit as st
from instagrapi import Client
import os
import requests
import base64
import cv2
from dotenv import load_dotenv
from openai import OpenAI

def carregar_variaveis_ambiente():
    """Carrega as variáveis de ambiente do arquivo .env."""
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

def gerar_imagem_por_texto(prompt):
    """Gera uma imagem usando o modelo GPT-Image-1 a partir de um texto."""
    client = OpenAI()
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt
    )
    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    image_path = "imagem_gerada.png"
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    return image_path

def gerar_imagem_por_edicao(prompt, imagens_upload):
    """Gera uma nova imagem a partir de imagens existentes e um prompt."""
    client = OpenAI()

    imagem_base = imagens_upload[0]

    result = client.images.edit(
        model="gpt-image-1",
        image=imagem_base,
        prompt=prompt
    )

    image_base64 = result.data[0].b64_json
    image_bytes = base64.b64decode(image_base64)

    image_path = "imagem_editada.png"
    with open(image_path, "wb") as f:
        f.write(image_bytes)

    return image_path

def converter_imagem_para_jpg(image_path):
    """Converte a imagem para JPG para garantir compatibilidade com Instagram."""
    img = cv2.imread(image_path)
    jpg_path = "imagem_final.jpg"
    cv2.imwrite(jpg_path, img, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
    return jpg_path

def login_instagram():
    """Realiza o login no Instagram usando as credenciais do .env."""
    username = os.getenv('INSTA_USER')
    password = os.getenv('INSTA_PASS')

    cl = Client()
    cl.login(username, password)
    return cl

def postar_imagem_instagram(cl, image_path, textoPost, textoStory):
    """Publica a imagem no feed e no story do Instagram."""
    cl.photo_upload(path=image_path, caption=textoPost)
    cl.photo_upload_to_story(path=image_path, caption=textoStory)

def verificar_senha(senha_input):
    """Verifica se a senha fornecida corresponde à senha de administrador."""
    senha_admin = os.getenv("SENHA_ADMIN")
    return senha_input == senha_admin

def main():
    """Função principal que orquestra o fluxo de criação e postagem com Streamlit."""
    carregar_variaveis_ambiente()
    st.title("Gerador de Imagens e Postagem no Instagram")

    if "senha_confirmada" not in st.session_state:
        st.session_state["senha_confirmada"] = False

    if not st.session_state["senha_confirmada"]:
        senha_input = st.text_input("Digite a senha de administrador para continuar:", type="password")
        if st.button("OK"):
            if verificar_senha(senha_input):
                st.session_state["senha_confirmada"] = True
                st.success("Senha confirmada! Você pode acessar as funcionalidades.")
            else:
                st.error("Senha incorreta. Por favor, tente novamente.")
        return

    tabs = st.tabs(["Geração de Imagem", "Postagem no Instagram"])

    with tabs[0]:
        modo = st.selectbox("Escolha o modo de geração de imagem:", ["Texto", "Imagem de Referência + Texto"])

        prompt = st.text_area("Digite o prompt para gerar a imagem:")

        imagens_upload = None
        if modo == "Imagem de Referência + Texto":
            imagens_upload = st.file_uploader("Envie até 10 imagens", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="file_uploader")

        if st.button("Gerar Imagem"):
            if modo == "Texto":
                caminho_png = gerar_imagem_por_texto(prompt)
                st.session_state['imagens_usadas'] = []
            elif modo == "Imagem de Referência + Texto" and imagens_upload:
                caminho_png = gerar_imagem_por_edicao(prompt, imagens_upload)
                st.session_state['imagens_usadas'] = imagens_upload
            else:
                st.error("Você deve enviar pelo menos uma imagem para o modo de edição.")
                return

            caminho_jpg = converter_imagem_para_jpg(caminho_png)
            st.session_state['caminho_imagem'] = caminho_jpg

            st.subheader("Pré-visualização da Imagem Gerada")
            st.image(caminho_jpg, caption="Imagem Gerada", use_column_width=True)

            if st.session_state['imagens_usadas']:
                st.subheader("Imagens Utilizadas na Criação")
                for img in st.session_state['imagens_usadas']:
                    st.image(img, width=150)

            st.success("Imagem gerada com sucesso!")

    with tabs[1]:
        if 'caminho_imagem' in st.session_state:
            st.image(st.session_state['caminho_imagem'], caption="Imagem pronta para postagem", use_column_width=True)

        textoPost = st.text_area("Digite o texto do post:")
        textoStory = st.text_area("Digite o texto do story:")

        if st.button("Postar no Instagram"):
            if 'caminho_imagem' not in st.session_state:
                st.error("Por favor, gere uma imagem antes de postar.")
                return

            caminho_jpg = st.session_state['caminho_imagem']
            cliente_instagram = login_instagram()
            postar_imagem_instagram(cliente_instagram, caminho_jpg, textoPost, textoStory)

            st.success("Imagem postada no feed e no story com sucesso!!")

if __name__ == "__main__":
    main()

