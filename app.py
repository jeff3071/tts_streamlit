from PIL import Image
import streamlit as st
import numpy as np
import requests
from xml.etree import ElementTree
import io
import os
import time
import json
from collections import defaultdict
from functools import lru_cache

@lru_cache
def _get_token(subscription_key: str, token_url: str) -> str:
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    response = requests.post(token_url, headers=headers)

    if response.status_code == 200:
        return response.content.decode()

def send_req(lang, speaker, text, speed, pitch, style):
    subscription_key = os.environ['subscription_key']
    
    token_url = "https://southeastasia.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
    api_url = "https://southeastasia.tts.speech.microsoft.com/cognitiveservices/v1"
    
    headers = {
            "Authorization": "Bearer "
            + _get_token(subscription_key, token_url),
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-160kbitrate-mono-mp3",
            "User-Agent": "gliacloud-speech",
        }
    xml_body = ElementTree.Element("speak", version="1.0")
    xml_body.set("xmlns", "https://www.w3.org/2001/10/synthesis")
    xml_body.set("xmlns:mstts", "http://www.w3.org/2001/mstts")
    xml_body.set("xmlns:emo", "http://www.w3.org/2009/10/emotionml")
    xml_body.set("xml:lang", lang)
    voice = ElementTree.SubElement(xml_body, "voice")
    voice.set("name", speaker)
    if style:
        voice = ElementTree.SubElement(voice, "mstts:express-as")
        voice.set("style", style)
    prosody = ElementTree.SubElement(voice, "prosody")
    prosody.set("rate", str(speed))
    prosody.set("pitch", str(pitch)+"%")
    prosody.text = text
    body = ElementTree.tostring(xml_body)

    response = requests.post(api_url, headers=headers, data=body)
    if response.status_code == 401:
        _get_token.cache_clear()
        headers[
            "Authorization"
        ] = f"Bearer {_get_token(subscription_key, token_url)}"
        response = requests.post(api_url, headers=headers, data=body)

    if response.status_code == 200:
        return response.content

def load_json():
    with open("list.json") as file:
        datalist = json.load(file)
        
    res = defaultdict(dict)
    for data in datalist:
        speaker = data["ShortName"]
        lang = data["Locale"]
        if "StyleList" in data.keys():
            styles = ["General"]+ data["StyleList"]
        else:
            styles = ["General"]
        res[lang].update({speaker: styles})
        
    return res

st.set_page_config(layout="wide", page_title="Image Background Remover")

st.markdown("\n")

data  = load_json()

col1, col2 = st.columns([8,2])
    
with col1:
    text = st.text_area("Enter text here:", height=480)
    
with col2:
    Language = st.selectbox("Language", data.keys(), index=43)
    Speaker = st.selectbox("Speaker", data[Language].keys())
    Speaking_type = st.selectbox("Speaking type", data[Language][Speaker])
    Speaking_speed = st.slider("Speaking speed", 0.0, 1.0, step=0.1)
    Pitch = st.slider("Pitch", -1.0, 1.0, step=0.1, value=0.0)
    subcol1, subcol2 = st.columns(2)
    with subcol1:
        play = st.button("Generate")
        
    if play and text:
        res = send_req(lang=Language, speaker=Speaker, text=text, speed=Speaking_speed, pitch=Pitch, style=Speaking_type)
        st.audio(res, format="audio/mp3")
        with subcol2:
            st.download_button(
                "Download", res, file_name="audio.mp3", mime="audio/mp3"
            )
        