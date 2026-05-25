import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO
from fpdf import FPDF
import os
import unicodedata
import base64
import hashlib
import tempfile
import html
import hmac
import re
import difflib
from PIL import Image, ImageDraw

try:
    import fitz
except ImportError:
    fitz = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(APP_DIR, "architecte.db")
LOGO_PATH = os.path.join(APP_DIR, "app_mhd_complet", "mourad.png")
HERO_IMAGE_PATH = os.path.join(APP_DIR, "app_mhd_complet", "villa_moderne.png")
BRAND_NAVY = (5, 31, 48)
BRAND_TEAL = (19, 145, 134)
BRAND_GOLD = (212, 168, 89)
BRAND_LIGHT = (244, 247, 248)

# Configuration de la page comme première commande Streamlit
st.set_page_config(page_title="Architecte - Devis Multi-Lots", layout="wide", initial_sidebar_state="expanded")

# CSS personnalisé pour une interface moderne sur le thème de l'architecture
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    .main {
        background: #f5f7f8;
        font-family: 'Roboto', sans-serif;
    }
    .stApp {
        background: transparent;
    }
    .card {
        background: white;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid rgba(5,31,48,0.08);
        box-shadow: 0 10px 28px rgba(5,31,48,0.08);
        margin-bottom: 20px;
    }
    .stButton > button {
        background: #051f30;
        color: white;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background: #139186;
        transform: translateY(-2px);
    }
    h1, h2, h3 {
        color: #051f30;
    }
    .sidebar .sidebar-content {
        background: #ffffff;
        box-shadow: 2px 0 5px rgba(0,0,0,0.1);
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] .stTextInput input {
        color: #051f30 !important;
        background: #ffffff !important;
        caret-color: #051f30 !important;
    }
    [data-testid="stSidebar"] input::placeholder,
    [data-testid="stSidebar"] textarea::placeholder {
        color: #667985 !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p {
        color: #051f30 !important;
    }
    .stProgress > div > div {
        background: #139186;
    }
    .delete-button > button {
        background: #e74c3c;
        color: white;
        border-radius: 5px;
    }
    .delete-button > button:hover {
        background: #c0392b;
        transform: translateY(-2px);
    }
    .app-logo-header {
        display: flex;
        align-items: center;
        gap: 22px;
        background: linear-gradient(120deg, #051f30 0%, #082b42 55%, #139186 100%);
        color: white;
    }
    .app-logo-header img {
        border-radius: 8px;
        max-height: 96px;
        object-fit: contain;
    }
    .app-logo-header h1,
    .app-logo-header p {
        color: white;
        margin-bottom: 0;
    }
    .stage-pill {
        display: inline-flex;
        align-items: center;
        padding: 6px 12px;
        border-radius: 999px;
        background: rgba(19,145,134,0.12);
        color: #09665f;
        font-weight: 700;
        margin: 4px 0 14px 0;
    }
    .design-kpi {
        background: white;
        border: 1px solid rgba(5,31,48,0.08);
        border-radius: 8px;
        padding: 16px 18px;
        box-shadow: 0 8px 24px rgba(5,31,48,0.07);
    }
    .design-kpi small {
        display: block;
        color: #5c6d78;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .03em;
    }
    .design-kpi strong {
        display: block;
        color: #139186;
        font-size: 1.45rem;
        margin-top: 6px;
    }
    .client-hero {
        text-align: center;
    }
    .client-hero img {
        margin: 0 auto 8px auto;
    }
    .client-summary p {
        font-size: 1.05rem;
        color: #415466;
        line-height: 1.55;
    }
    .client-progress-row {
        margin: 14px 0 18px 0;
    }
    .client-progress-head {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 7px;
        color: #233445;
    }
    .client-progress-track {
        height: 18px;
        background: #edf1f5;
        border-radius: 999px;
        overflow: hidden;
        border: 1px solid #d8e0e8;
    }
    .client-progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #051f30, #139186);
        border-radius: 999px;
    }
    .deadline-panel {
        margin: 12px 0 16px 0;
        padding: 14px 16px;
        background: #ffffff;
        border: 1px solid #dfe6ea;
        border-radius: 8px;
    }
    .deadline-head {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        color: #233445;
        font-weight: 700;
        margin-bottom: 9px;
    }
    .deadline-track {
        height: 18px;
        border-radius: 999px;
        background: linear-gradient(90deg, #139186 0%, #d4a859 58%, #c84848 100%);
        overflow: hidden;
        position: relative;
        border: 1px solid #ccd7dc;
    }
    .deadline-mask {
        position: absolute;
        top: 0;
        right: 0;
        height: 100%;
        background: rgba(236, 241, 244, 0.88);
    }
    .deadline-marker {
        position: absolute;
        top: -4px;
        width: 4px;
        height: 26px;
        background: #051f30;
        border-radius: 4px;
        box-shadow: 0 0 0 2px rgba(255,255,255,.8);
    }
    .deadline-foot {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        color: #60717c;
        font-size: .88rem;
        margin-top: 7px;
    }
    .deadline-alert {
        padding: 10px 12px;
        border-radius: 8px;
        margin: 8px 0;
        border: 1px solid transparent;
        font-weight: 700;
    }
    .deadline-alert.warning {
        color: #7a4a00;
        background: #fff4db;
        border-color: #efd092;
    }
    .deadline-alert.danger {
        color: #7f1d1d;
        background: #fde8e8;
        border-color: #efb1b1;
    }
    .tracking-report {
        background: #fff;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #dfe6ea;
        box-shadow: 0 10px 28px rgba(5,31,48,0.08);
        margin-top: 18px;
    }
    .tracking-header,
    .tracking-row {
        display: grid;
        grid-template-columns: 70px minmax(230px, 2fr) 90px 90px 95px 120px 150px 150px;
        align-items: stretch;
    }
    .tracking-header {
        background: #052f32;
        color: white;
        font-weight: 700;
        text-transform: uppercase;
        font-size: .8rem;
        letter-spacing: .02em;
    }
    .tracking-cell {
        padding: 14px 16px;
        border-right: 1px solid #dfe6ea;
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 86px;
    }
    .tracking-header .tracking-cell {
        min-height: auto;
        padding: 12px 14px;
    }
    .tracking-row {
        border-bottom: 1px solid #dfe6ea;
    }
    .tracking-row:last-child {
        border-bottom: none;
    }
    .tracking-lot {
        color: white;
        flex-direction: column;
        gap: 6px;
        font-weight: 800;
        font-size: 1.15rem;
    }
    .tracking-lot small {
        font-size: .72rem;
        opacity: .9;
    }
    .tracking-designation {
        justify-content: flex-start;
        align-items: flex-start;
        flex-direction: column;
    }
    .tracking-designation strong {
        color: #051f30;
        font-size: 1rem;
        line-height: 1.25;
    }
    .tracking-designation span {
        color: #687984;
        margin-top: 4px;
        line-height: 1.25;
    }
    .tracking-total {
        color: #139186;
        font-weight: 800;
    }
    .tracking-ring {
        width: 86px;
        height: 86px;
        border-radius: 50%;
        display: grid;
        place-items: center;
        background: conic-gradient(var(--accent) calc(var(--pct) * 1%), #e6e7e9 0);
        position: relative;
        font-weight: 800;
        color: #051f30;
    }
    .tracking-ring::before {
        content: "";
        position: absolute;
        inset: 9px;
        background: white;
        border-radius: 50%;
        box-shadow: inset 0 0 0 1px #f1f3f4;
    }
    .tracking-ring span {
        position: relative;
        z-index: 1;
    }
    .tracking-photo {
        width: 116px;
        height: 82px;
        border-radius: 8px;
        object-fit: cover;
        background: #f2f4f5;
    }
    .tracking-placeholder {
        width: 116px;
        height: 82px;
        border-radius: 8px;
        background: #f4f5f6;
        color: #687984;
        display: grid;
        place-items: center;
        text-align: center;
        font-size: .78rem;
    }
    .finance-timeline {
        display: grid;
        gap: 10px;
        margin-top: 14px;
    }
    .finance-summary-panel {
        display: grid;
        grid-template-columns: 1fr 210px;
        gap: 20px;
        align-items: center;
        margin-top: 14px;
        padding: 18px;
        border-radius: 8px;
        background: linear-gradient(135deg, #ffffff 0%, #f6faf9 100%);
        border: 1px solid #dfe6ea;
        box-shadow: 0 10px 28px rgba(5,31,48,0.08);
    }
    .finance-summary-bars {
        display: grid;
        gap: 14px;
    }
    .finance-summary-line {
        display: grid;
        grid-template-columns: 160px 1fr 120px;
        gap: 12px;
        align-items: center;
    }
    .finance-summary-label {
        color: #051f30;
        font-weight: 800;
    }
    .finance-summary-value {
        color: #051f30;
        font-weight: 800;
        text-align: right;
    }
    .finance-summary-status {
        min-height: 116px;
        border-radius: 8px;
        display: grid;
        place-items: center;
        text-align: center;
        padding: 14px;
        color: white;
        font-weight: 800;
    }
    .finance-summary-status.positive {
        background: linear-gradient(135deg, #139186, #0b5d58);
    }
    .finance-summary-status.negative {
        background: linear-gradient(135deg, #c84848, #7e2727);
    }
    .finance-summary-status strong {
        display: block;
        font-size: 1.45rem;
        margin-top: 6px;
    }
    .finance-row {
        display: grid;
        grid-template-columns: 120px 1fr 140px;
        gap: 14px;
        align-items: center;
        padding: 12px 14px;
        background: #ffffff;
        border: 1px solid #dfe6ea;
        border-radius: 8px;
        box-shadow: 0 6px 18px rgba(5,31,48,0.06);
    }
    .finance-date {
        color: #051f30;
        font-weight: 800;
    }
    .finance-bars {
        display: grid;
        gap: 7px;
    }
    .finance-bar {
        height: 10px;
        border-radius: 999px;
        background: #eef2f4;
        overflow: hidden;
    }
    .finance-fill {
        height: 100%;
        border-radius: 999px;
    }
    .finance-fill.advance {
        background: linear-gradient(90deg, #139186, #7dd3c7);
    }
    .finance-fill.payment {
        background: linear-gradient(90deg, #051f30, #2989ca);
    }
    .finance-balance {
        text-align: right;
        font-weight: 800;
    }
    .finance-balance.positive {
        color: #139186;
    }
    .finance-balance.negative {
        color: #c84848;
    }
    @media (max-width: 1100px) {
        .tracking-report {
            overflow-x: auto;
        }
        .tracking-header,
        .tracking-row {
            min-width: 980px;
        }
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(19,145,134,.10), transparent 28rem),
            linear-gradient(180deg, #f6f8f8 0%, #ffffff 42%, #f4f7f7 100%);
    }
    .block-container {
        padding-top: 1.6rem;
        max-width: 1220px;
    }
    .card {
        border: 1px solid rgba(5,31,48,.08);
        border-radius: 8px;
        box-shadow: 0 18px 48px rgba(5,31,48,.08);
    }
    .mhd-hero {
        position: relative;
        overflow: hidden;
        min-height: 340px;
        border-radius: 8px;
        margin-bottom: 28px;
        background: #051f30;
        border: 1px solid rgba(255,255,255,.12);
        box-shadow: 0 30px 80px rgba(0,0,0,.34);
    }
    .mhd-hero-top {
        position: relative;
        min-height: 218px;
        background: linear-gradient(118deg, rgba(6,27,42,.98) 0%, rgba(9,45,67,.96) 43%, #ffffff 43.2%, #ffffff 45.7%, #139186 46%, #139186 48%, transparent 48.2%);
    }
    .mhd-hero-brand {
        position: absolute;
        left: 34px;
        top: 26px;
        width: 42%;
        color: #ffffff;
        z-index: 2;
    }
    .mhd-hero-brand-row {
        display: flex;
        align-items: center;
        gap: 18px;
    }
    .mhd-hero-logo {
        max-width: 104px;
        max-height: 104px;
        object-fit: contain;
        filter: drop-shadow(0 12px 28px rgba(0,0,0,.24));
    }
    .mhd-brand-name {
        color: #d4a859;
        font-size: clamp(2.2rem, 5vw, 4.2rem);
        line-height: .9;
        font-weight: 300;
        letter-spacing: 0;
    }
    .mhd-brand-subtitle {
        margin-top: 8px;
        color: rgba(255,255,255,.94);
        font-size: .95rem;
        text-transform: uppercase;
        letter-spacing: .08em;
    }
    .mhd-brand-person {
        margin-top: 8px;
        color: #ffffff;
        font-size: 1.05rem;
        text-transform: uppercase;
        letter-spacing: .10em;
        font-weight: 700;
    }
    .mhd-villa-scene {
        position: absolute;
        right: 0;
        top: 0;
        width: 54%;
        height: 252px;
        background:
            linear-gradient(90deg, rgba(5,31,48,.12), rgba(5,31,48,0)),
            var(--hero-photo, linear-gradient(135deg, #cfd8dd 0%, #f6f7f6 42%, #87959c 100%));
        background-size: cover;
        background-position: center;
        clip-path: polygon(17% 0, 100% 0, 100% 100%, 0 100%);
    }
    .mhd-villa {
        position: absolute;
        right: 44px;
        top: 38px;
        width: min(390px, 72%);
        height: 132px;
    }
    .mhd-villa::before,
    .mhd-villa::after {
        content: "";
        position: absolute;
        background: #eef1f2;
        box-shadow: 0 18px 40px rgba(5,31,48,.25);
    }
    .mhd-villa::before {
        width: 100%;
        height: 86px;
        left: 0;
        top: 34px;
    }
    .mhd-villa::after {
        width: 64%;
        height: 56px;
        right: 0;
        top: 0;
    }
    .mhd-window {
        position: absolute;
        z-index: 2;
        background: linear-gradient(180deg, #1b2a31, #07131a);
        border: 4px solid #d8dddf;
        box-shadow: inset 0 0 28px rgba(212,168,89,.28);
    }
    .mhd-window.one { left: 18px; top: 54px; width: 108px; height: 54px; }
    .mhd-window.two { left: 142px; top: 54px; width: 78px; height: 54px; }
    .mhd-window.three { right: 22px; top: 18px; width: 96px; height: 45px; }
    .mhd-hero-title {
        padding: 34px 38px 36px;
        background: linear-gradient(105deg, #ffffff 0%, #ffffff 52%, rgba(255,255,255,.82) 52.3%, rgba(255,255,255,0) 70%);
        clip-path: polygon(0 0, 52% 0, 64% 100%, 0 100%);
    }
    .mhd-hero-title h1 {
        margin: 0;
        color: #061b2a;
        font-size: clamp(2rem, 4.8vw, 3.55rem);
        line-height: .98;
        font-weight: 900;
        text-transform: uppercase;
    }
    .mhd-hero-title strong {
        display: block;
        margin-top: 12px;
        color: #139186;
        font-size: clamp(1.25rem, 3.1vw, 2.15rem);
        line-height: 1;
        font-weight: 900;
        text-transform: uppercase;
    }
    .mhd-gold-line {
        width: 150px;
        height: 4px;
        background: #d4a859;
        margin-top: 18px;
    }
    .mhd-mode-badge {
        display: inline-flex;
        align-items: center;
        margin-bottom: 12px;
        padding: 6px 12px;
        border-radius: 999px;
        background: rgba(19,145,134,.12);
        color: #08716a;
        font-size: .78rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: .08em;
    }
    .app-logo-header {
        display: none;
    }
    .client-hero {
        display: none;
    }
    .design-kpi {
        min-height: 104px;
        padding: 18px 20px;
        background: rgba(255,255,255,.92);
        border: 1px solid rgba(5,31,48,.08);
        box-shadow: 0 14px 34px rgba(5,31,48,.08);
    }
    .design-kpi small {
        color: #101d29;
        font-size: .78rem;
    }
    .design-kpi strong {
        color: #0b756f;
        font-size: clamp(1.3rem, 2vw, 1.8rem);
    }
    .tracking-report {
        border-radius: 8px;
        border: 1px solid rgba(5,31,48,.10);
        box-shadow: 0 22px 55px rgba(5,31,48,.10);
    }
    .tracking-header {
        background: linear-gradient(180deg, #073a3d, #05282d);
        font-size: .82rem;
    }
    .tracking-header .tracking-cell {
        color: #ffffff;
    }
    .tracking-cell {
        border-right: 1px solid rgba(5,31,48,.10);
        min-height: 104px;
    }
    .tracking-row {
        background: #ffffff;
    }
    .tracking-row:hover {
        background: #fbfdfd;
    }
    .tracking-lot {
        font-size: 1.38rem;
        text-shadow: 0 2px 12px rgba(0,0,0,.18);
    }
    .tracking-designation strong {
        font-size: 1.05rem;
    }
    .tracking-total {
        font-size: 1.02rem;
    }
    .tracking-ring {
        width: 88px;
        height: 88px;
        box-shadow: inset 0 0 0 8px rgba(255,255,255,.70), 0 8px 24px rgba(5,31,48,.08);
    }
    .tracking-photo,
    .tracking-placeholder {
        width: 128px;
        height: 92px;
        border-radius: 8px;
    }
    .report-kpis {
        display: grid;
        grid-template-columns: 1.25fr 1fr 1fr;
        gap: 16px;
        margin-top: 22px;
    }
    .report-kpi-main {
        grid-row: span 2;
        min-height: 178px;
        display: flex;
        align-items: center;
        gap: 22px;
        background: radial-gradient(circle at 18% 50%, rgba(19,145,134,.42), transparent 5.5rem), linear-gradient(135deg, #061b2a, #08314b);
        color: #ffffff;
    }
    .report-kpi-main small {
        color: #ffffff;
    }
    .report-kpi-main strong {
        color: #2dc6b8;
        font-size: clamp(2rem, 3vw, 2.8rem);
    }
    .report-kpi-icon {
        width: 92px;
        height: 92px;
        border-radius: 999px;
        display: grid;
        place-items: center;
        background: linear-gradient(135deg, #139186, #51d1c4);
        color: #ffffff;
        font-size: 2.15rem;
        font-weight: 900;
        flex: 0 0 auto;
    }
    @media (max-width: 760px) {
        .mhd-hero {
            min-height: 300px;
        }
        .mhd-hero-top {
            min-height: 150px;
            background: linear-gradient(126deg, #061b2a 0%, #092d43 66%, #139186 66.5%, #139186 69%, transparent 69.5%);
        }
        .mhd-hero-brand {
            left: 18px;
            top: 20px;
            width: 78%;
        }
        .mhd-hero-logo {
            max-width: 70px;
            max-height: 70px;
        }
        .mhd-villa-scene {
            opacity: .32;
            width: 72%;
        }
        .mhd-villa {
            right: 12px;
            width: 82%;
        }
        .mhd-hero-title {
            clip-path: none;
            padding: 22px 20px 24px;
        }
        .report-kpis {
            grid-template-columns: 1fr;
        }
        .report-kpi-main {
            grid-row: auto;
        }
    }
    [data-testid="stAppViewContainer"] {
        background:
            linear-gradient(180deg, rgba(5,31,48,.93), rgba(8,46,59,.88) 34%, rgba(244,247,248,.96) 34.2%, #f7faf9 100%),
            radial-gradient(circle at 84% 12%, rgba(212,168,89,.22), transparent 23rem),
            radial-gradient(circle at 6% 18%, rgba(19,145,134,.24), transparent 21rem) !important;
    }
    html,
    body,
    .stApp,
    .main,
    section.main,
    [data-testid="stApp"],
    [data-testid="stDecoration"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"] {
        background-color: #051f30 !important;
    }
    .stApp,
    .main,
    section.main,
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background-image:
            linear-gradient(180deg, rgba(5,31,48,.98) 0%, rgba(5,31,48,.94) 260px, rgba(244,247,248,.98) 261px, #f7faf9 100%),
            radial-gradient(circle at 85px 90px, rgba(19,145,134,.34), transparent 280px),
            radial-gradient(circle at 88% 120px, rgba(212,168,89,.28), transparent 340px) !important;
        background-attachment: fixed !important;
    }
    [data-testid="stMainBlockContainer"],
    .block-container {
        background: transparent !important;
    }
    .mhd-version-badge {
        position: fixed;
        right: 14px;
        bottom: 12px;
        z-index: 9999;
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(5,31,48,.88);
        color: #ffffff;
        border: 1px solid rgba(255,255,255,.18);
        font-size: 11px;
        font-weight: 800;
        letter-spacing: .04em;
        box-shadow: 0 10px 26px rgba(0,0,0,.22);
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="stToolbar"] {
        right: 1rem;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #061b2a, #082f3a) !important;
        border-right: 1px solid rgba(255,255,255,.12);
    }
    [data-testid="stSidebar"] * {
        color: rgba(255,255,255,.92);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        background: rgba(255,255,255,.08);
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 6px;
    }
    .main .block-container {
        padding-top: 2.2rem;
    }
    .card,
    div[data-testid="stExpander"],
    div[data-testid="stForm"] {
        background: rgba(255,255,255,.92) !important;
        border: 1px solid rgba(255,255,255,.72) !important;
        box-shadow: 0 22px 52px rgba(5,31,48,.13) !important;
        backdrop-filter: blur(14px);
    }
    h1, h2, h3 {
        letter-spacing: 0;
    }
    .stTextInput input,
    .stNumberInput input,
    .stDateInput input,
    textarea {
        border-radius: 8px !important;
        border: 1px solid rgba(5,31,48,.14) !important;
        background: rgba(255,255,255,.96) !important;
        box-shadow: 0 8px 22px rgba(5,31,48,.06);
    }
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 8px !important;
        border: 1px solid rgba(255,255,255,.14) !important;
        background: linear-gradient(135deg, #051f30, #139186) !important;
        box-shadow: 0 14px 30px rgba(5,31,48,.20);
        font-weight: 800;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 18px 36px rgba(5,31,48,.24);
    }
    .mhd-hero {
        min-height: 380px;
        margin-bottom: 34px;
        background: #f4f7f8 !important;
        border: 1px solid rgba(255,255,255,.70);
    }
    .mhd-hero-photo {
        position: absolute !important;
        inset: 0 !important;
        width: 100% !important;
        height: 100% !important;
        max-width: none !important;
        min-width: 100% !important;
        min-height: 100% !important;
        object-fit: cover !important;
        object-position: center center !important;
        z-index: 0 !important;
    }
    .mhd-hero::after {
        content: "";
        position: absolute;
        inset: 0;
        z-index: 1;
        background: linear-gradient(90deg, rgba(255,255,255,.94) 0%, rgba(255,255,255,.80) 31%, rgba(255,255,255,.12) 52%, rgba(5,31,48,.05) 100%);
        pointer-events: none;
    }
    .mhd-hero-top {
        min-height: 190px;
        background: transparent !important;
        position: relative;
        z-index: 2;
    }
    .mhd-hero-brand {
        top: 46px;
        left: 46px;
        width: 34%;
        color: #101d29;
    }
    .mhd-hero-logo {
        display: none;
    }
    .mhd-brand-name {
        color: #2f2619;
        font-size: clamp(2.6rem, 5vw, 4.6rem);
        font-weight: 300;
    }
    .mhd-brand-subtitle {
        color: #101d29;
        font-weight: 900;
        letter-spacing: .34em;
    }
    .mhd-brand-person {
        color: #101d29;
        font-size: .82rem;
        letter-spacing: .42em;
        opacity: .72;
    }
    .mhd-villa-scene,
    .mhd-villa,
    .mhd-window {
        display: none !important;
    }
    .mhd-hero-title {
        position: absolute;
        left: 0;
        bottom: 0;
        z-index: 2;
        width: min(620px, 58%);
        padding: 28px 42px 34px;
        background: linear-gradient(100deg, rgba(255,255,255,.96) 0%, rgba(255,255,255,.90) 78%, rgba(255,255,255,0) 100%) !important;
        clip-path: none !important;
    }
    .mhd-hero-title h1 {
        font-size: clamp(2rem, 4vw, 3.25rem);
    }
    .mhd-hero-title strong {
        font-size: clamp(1.15rem, 2.4vw, 1.8rem);
    }
    .mhd-mode-badge {
        background: rgba(19,145,134,.14);
    }
    @media (max-width: 760px) {
        [data-testid="stAppViewContainer"],
        .stApp,
        .main,
        section.main,
        [data-testid="stMain"] {
            background-image:
                linear-gradient(180deg, rgba(5,31,48,.98) 0%, rgba(5,31,48,.92) 210px, rgba(244,247,248,.98) 211px, #f7faf9 100%) !important;
        }
        .main .block-container,
        .block-container,
        [data-testid="stMainBlockContainer"] {
            padding-left: 0.8rem !important;
            padding-right: 0.8rem !important;
            padding-top: 1rem !important;
        }
        .mhd-hero {
            min-height: 330px !important;
            margin-bottom: 22px !important;
            border-radius: 8px;
        }
        .mhd-hero-photo {
            object-position: 62% center !important;
        }
        .mhd-hero::after {
            background: linear-gradient(180deg, rgba(255,255,255,.84) 0%, rgba(255,255,255,.50) 34%, rgba(5,31,48,.08) 58%, rgba(5,31,48,.18) 100%);
        }
        .mhd-hero-top {
            min-height: 150px !important;
        }
        .mhd-hero-brand {
            top: 24px !important;
            left: 22px !important;
            width: 78% !important;
        }
        .mhd-brand-name {
            font-size: 2.45rem !important;
        }
        .mhd-brand-subtitle {
            font-size: .78rem;
            letter-spacing: .22em;
        }
        .mhd-brand-person {
            font-size: .68rem;
            letter-spacing: .26em;
        }
        .mhd-hero-title {
            width: 100% !important;
            padding: 18px 20px 22px !important;
            background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(255,255,255,.98)) !important;
        }
        .mhd-hero-title h1 {
            font-size: 1.85rem !important;
            line-height: 1.05;
        }
        .mhd-hero-title strong {
            font-size: 1.05rem !important;
            margin-top: 8px;
        }
        .mhd-gold-line {
            width: 92px;
            margin-top: 12px;
        }
        .card {
            padding: 16px !important;
        }
        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        textarea {
            min-height: 44px;
            font-size: 16px !important;
        }
        .tracking-header,
        .tracking-row {
            min-width: 980px;
        }
        .finance-summary-panel,
        .finance-summary-line {
            grid-template-columns: 1fr !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialisation de la base de données SQLite
def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    c = conn.cursor()
    # Tableaux clients
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT UNIQUE NOT NULL
        )
    ''')
    # Tableaux projets
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            project_name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            project_status TEXT DEFAULT 'devis_initial',
            validated_at TEXT,
            deadline_alerts_enabled INTEGER DEFAULT 0,
            FOREIGN KEY (client_id) REFERENCES clients(client_id)
        )
    ''')
    c.execute("PRAGMA table_info(projects)")
    project_columns = [info[1] for info in c.fetchall()]
    if 'project_status' not in project_columns:
        c.execute("ALTER TABLE projects ADD COLUMN project_status TEXT DEFAULT 'devis_initial'")
    if 'validated_at' not in project_columns:
        c.execute("ALTER TABLE projects ADD COLUMN validated_at TEXT")
    if 'deadline_alerts_enabled' not in project_columns:
        c.execute("ALTER TABLE projects ADD COLUMN deadline_alerts_enabled INTEGER DEFAULT 0")
    c.execute("SELECT COUNT(*) FROM projects WHERE project_status IS NULL OR project_status = ''")
    if c.fetchone()[0]:
        c.execute("UPDATE projects SET project_status = 'devis_initial' WHERE project_status IS NULL OR project_status = ''")
    # Tableaux détails du projet (dernière version)
    c.execute('''
        CREATE TABLE IF NOT EXISTS project_details (
            detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            lot TEXT,
            designation TEXT,
            unite TEXT,
            quantite REAL,
            prix_unitaire REAL,
            cout_total REAL,
            duree INTEGER,
            debut TEXT,
            fin TEXT,
            jours_ecoules INTEGER,
            retard INTEGER,
            avancement INTEGER,
            paiement REAL,
            image TEXT,
            updated_at TEXT,
            UNIQUE(project_id, lot, designation),
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    ''')
    # Tableaux historique du projet
    c.execute('''
        CREATE TABLE IF NOT EXISTS project_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            lot TEXT,
            designation TEXT,
            avancement INTEGER,
            paiement REAL,
            image TEXT,
            updated_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    ''')
    # Vérifier et ajouter la colonne paiement si elle n'existe pas
    c.execute("PRAGMA table_info(project_history)")
    columns = [info[1] for info in c.fetchall()]
    if 'paiement' not in columns:
        c.execute('ALTER TABLE project_history ADD COLUMN paiement REAL')
    # Tableaux avances perçues
    c.execute('''
        CREATE TABLE IF NOT EXISTS project_advances (
            advance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            advance_amount REAL,
            updated_at TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(project_id)
        )
    ''')
    c.execute("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'project_advances'")
    advances_schema = c.fetchone()
    if advances_schema and "UNIQUE(project_id)" in advances_schema[0].replace(" ", ""):
        c.execute("ALTER TABLE project_advances RENAME TO project_advances_old")
        c.execute('''
            CREATE TABLE project_advances (
                advance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                advance_amount REAL,
                updated_at TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id)
            )
        ''')
        c.execute('''
            INSERT INTO project_advances (advance_id, project_id, advance_amount, updated_at)
            SELECT advance_id, project_id, advance_amount, updated_at
            FROM project_advances_old
        ''')
        c.execute("DROP TABLE project_advances_old")
    # Accès client au tableau de suivi
    c.execute('''
        CREATE TABLE IF NOT EXISTS client_portal_users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER UNIQUE,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(client_id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def db_connect():
    return sqlite3.connect(DB_PATH, timeout=15)

def safe_text(s):
    return unicodedata.normalize('NFKD', str(s)).encode('latin-1', 'ignore').decode('latin-1')

def password_hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def format_date(value):
    if not value:
        return ""
    try:
        return datetime.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except ValueError:
        return str(value)

def normalize_label(value):
    return unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii").lower().strip()

def save_lot_designation(lot, designation):
    lot = str(lot or "").strip()
    designation = str(designation or "").strip()
    if not lot or not designation:
        return False, "Veuillez renseigner le lot et la désignation."
    new_row = pd.DataFrame([{"lots": lot, "DESIGNATIONS": designation}])
    file_path = os.path.join(APP_DIR, "lot_et_designation_par_lot.xlsx")
    if os.path.exists(file_path):
        current_df = pd.read_excel(file_path)
    else:
        current_df = pd.DataFrame(columns=["lots", "DESIGNATIONS"])
    current_df.columns = current_df.columns.str.strip()
    current_df = pd.concat([current_df, new_row], ignore_index=True)
    before = len(current_df)
    current_df.drop_duplicates(subset=["lots", "DESIGNATIONS"], inplace=True)
    current_df.to_excel(file_path, index=False)
    st.session_state.lots_db = pd.concat([st.session_state.lots_db, new_row], ignore_index=True)
    st.session_state.lots_db.drop_duplicates(subset=["lots", "DESIGNATIONS"], inplace=True)
    if len(current_df) == before:
        return True, f"« {designation} » existe déjà dans « {lot} »."
    return True, f"« {designation} » ajouté à « {lot} »."

def find_lot_for_designation(designation, lots_db):
    if lots_db.empty:
        return "Divers"
    norm_target = normalize_label(designation)
    lots_db = lots_db.copy()
    lots_db["norm"] = lots_db["DESIGNATIONS"].apply(normalize_label)
    exact = lots_db[lots_db["norm"] == norm_target]
    if not exact.empty:
        return exact.iloc[0]["lots"]
    choices = lots_db["norm"].tolist()
    match = difflib.get_close_matches(norm_target, choices, n=1, cutoff=0.55)
    if match:
        return lots_db[lots_db["norm"] == match[0]].iloc[0]["lots"]
    return "Divers"

def extract_text_from_uploaded_quote(uploaded_file):
    raw = uploaded_file.getvalue()
    name = uploaded_file.name.lower()
    if name.endswith(".pdf") and fitz is not None:
        text_parts = []
        with fitz.open(stream=raw, filetype="pdf") as doc:
            for page in doc:
                text_parts.append(page.get_text("text"))
        text = "\n".join(text_parts).strip()
        if text:
            return text, "PDF texte lu automatiquement."
    if pytesseract is None:
        return "", "OCR indisponible : installez pytesseract + Tesseract pour lire les scans image."
    try:
        if name.endswith(".pdf") and fitz is not None:
            text_parts = []
            with fitz.open(stream=raw, filetype="pdf") as doc:
                for page in doc:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    image = Image.open(BytesIO(pix.tobytes("png")))
                    text_parts.append(pytesseract.image_to_string(image, lang="fra+eng"))
            return "\n".join(text_parts).strip(), "PDF scanné lu par OCR."
        image = Image.open(BytesIO(raw))
        return pytesseract.image_to_string(image, lang="fra+eng").strip(), "Image lue par OCR."
    except Exception as exc:
        return "", f"Lecture impossible : {exc}"

def parse_quote_text_to_rows(text, lots_db):
    rows = []
    units_pattern = r"(m2|m²|ml|m\.l|u|unite|unité|forfait|fft)"
    number_pattern = r"(\d+(?:[,.]\d+)?)"
    for raw_line in text.splitlines():
        line = " ".join(raw_line.strip().split())
        if len(line) < 4:
            continue
        nums = re.findall(number_pattern, line)
        if not nums:
            continue
        unit_match = re.search(units_pattern, line, flags=re.IGNORECASE)
        unit = "m²"
        if unit_match and normalize_label(unit_match.group(1)).replace(".", "") == "ml":
            unit = "ML"
        qty = float(nums[0].replace(",", ".")) if nums else 1.0
        pu = float(nums[-1].replace(",", ".")) if len(nums) >= 2 else 0.0
        designation = re.sub(number_pattern, " ", line)
        designation = re.sub(units_pattern, " ", designation, flags=re.IGNORECASE)
        designation = re.sub(r"[-:;|]+", " ", designation)
        designation = " ".join(designation.split())
        if not designation:
            designation = line
        lot = find_lot_for_designation(designation, lots_db)
        rows.append({
            "Lot": lot,
            "Désignation": designation[:180],
            "Unité": unit,
            "Quantité": qty,
            "Prix Unitaire": pu,
            "Coût Total": qty * pu,
        })
    return pd.DataFrame(rows)

def deadline_status(duree, debut, avancement):
    today = datetime.today().date()
    if isinstance(debut, datetime):
        start_date = debut.date()
    elif hasattr(debut, "isoformat") and not isinstance(debut, str):
        start_date = debut
    else:
        try:
            start_date = datetime.fromisoformat(str(debut)).date()
        except ValueError:
            start_date = today
    duree = max(1, int(duree or 1))
    percent_done = max(0, min(100, int(avancement or 0)))
    end_date = start_date + timedelta(days=duree)
    elapsed_days = max(0, (today - start_date).days)
    remaining_days = (end_date - today).days
    time_percent = max(0, min(100, int((elapsed_days / duree) * 100)))
    alert_type = ""
    alert_text = ""
    if remaining_days < 0 and percent_done < 100:
        alert_type = "danger"
        alert_text = f"Délai dépassé de {abs(remaining_days)} jour(s) avec {percent_done}% d'avancement."
    elif 0 <= remaining_days <= 2 and percent_done < 50:
        alert_type = "warning"
        alert_text = f"Fin prévue dans {remaining_days} jour(s), avancement encore bas ({percent_done}%)."
    return {
        "start": start_date,
        "end": end_date,
        "elapsed_days": elapsed_days,
        "remaining_days": remaining_days,
        "time_percent": time_percent,
        "alert_type": alert_type,
        "alert_text": alert_text,
    }

def render_deadline_bar(label, status):
    mask_width = 100 - status["time_percent"]
    st.markdown(
        f"""
        <div class="deadline-panel">
            <div class="deadline-head">
                <span>{html.escape(label)}</span>
                <span>{status["time_percent"]}% du délai consommé</span>
            </div>
            <div class="deadline-track">
                <div class="deadline-mask" style="width:{mask_width}%"></div>
                <div class="deadline-marker" style="left:calc({status["time_percent"]}% - 2px)"></div>
            </div>
            <div class="deadline-foot">
                <span>Début : {format_date(status["start"].isoformat())}</span>
                <span>Fin : {format_date(status["end"].isoformat())}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if status["alert_text"]:
        st.markdown(
            f"<div class='deadline-alert {status['alert_type']}'>{html.escape(status['alert_text'])}</div>",
            unsafe_allow_html=True
        )

def render_deadline_alert_summary(df):
    alerts = df[df["Alerte délai"].astype(str).str.len() > 0]
    if alerts.empty:
        st.success("Aucune alerte de délai active pour les lots suivis.")
        return
    for _, row in alerts.iterrows():
        alert_class = "danger" if "dépassé" in row["Alerte délai"].lower() else "warning"
        st.markdown(
            f"<div class='deadline-alert {alert_class}'>{html.escape(row['Lot'])} - {html.escape(row['Désignation'])} : {html.escape(row['Alerte délai'])}</div>",
            unsafe_allow_html=True
        )

def get_total_advances(cursor, project_id):
    cursor.execute("SELECT COALESCE(SUM(advance_amount), 0) FROM project_advances WHERE project_id = ?", (project_id,))
    return cursor.fetchone()[0] or 0.0

def get_project_total(cursor, project_id):
    cursor.execute("SELECT COALESCE(SUM(cout_total), 0) FROM project_details WHERE project_id = ?", (project_id,))
    return cursor.fetchone()[0] or 0.0

def should_add_history_entry(cursor, project_id, row):
    cursor.execute('''
        SELECT avancement, paiement, image
        FROM project_history
        WHERE project_id = ? AND lot = ? AND designation = ?
        ORDER BY updated_at DESC, history_id DESC
        LIMIT 1
    ''', (project_id, row["Lot"], row["Désignation"]))
    latest = cursor.fetchone()
    new_avancement = int(row["Avancement (%)"] or 0)
    new_paiement = float(row["Paiement Engagé"] or 0)
    new_image = row["Image"] or ""
    if not latest:
        return new_avancement > 0 or new_paiement > 0 or bool(new_image)
    old_avancement = int(latest[0] or 0)
    old_paiement = float(latest[1] or 0)
    old_image = latest[2] or ""
    return (
        old_avancement != new_avancement
        or abs(old_paiement - new_paiement) > 0.01
        or old_image != new_image
    )

def build_financing_timeline(cursor, project_id):
    events = []
    cursor.execute('''
        SELECT advance_amount, updated_at
        FROM project_advances
        WHERE project_id = ?
        ORDER BY updated_at ASC
    ''', (project_id,))
    for amount, updated_at in cursor.fetchall():
        events.append({
            "date": datetime.fromisoformat(updated_at),
            "type": "advance",
            "amount": float(amount or 0),
            "key": None,
        })
    cursor.execute('''
        SELECT lot, designation, paiement, updated_at
        FROM project_history
        WHERE project_id = ?
        ORDER BY updated_at ASC, history_id ASC
    ''', (project_id,))
    for lot, designation, paiement, updated_at in cursor.fetchall():
        events.append({
            "date": datetime.fromisoformat(updated_at),
            "type": "payment",
            "amount": float(paiement or 0),
            "key": (lot, designation),
        })
    events.sort(key=lambda item: item["date"])
    cumulative_advances = 0.0
    latest_payments = {}
    timeline = []
    for event in events:
        if event["type"] == "advance":
            cumulative_advances += event["amount"]
            label = "Avance perçue"
        else:
            latest_payments[event["key"]] = event["amount"]
            label = "Paiement engagé"
        total_payments = sum(latest_payments.values())
        balance = cumulative_advances - total_payments
        timeline.append({
            "Date": event["date"],
            "Evénement": label,
            "Montant événement": event["amount"],
            "Avances cumulées": cumulative_advances,
            "Paiements engagés cumulés": total_payments,
            "Solde financement": balance,
            "Statut": "Excédent" if balance >= 0 else "Besoin",
        })
    return pd.DataFrame(timeline)

def generate_financing_pdf(timeline_df, selected_client, selected_project):
    pdf = FPDF()
    pdf.add_page()
    add_pdf_header(pdf, "Rapport financement", selected_client, selected_project)
    if timeline_df.empty:
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 10, safe_text("Aucun mouvement financier disponible."), ln=True)
    else:
        last_row = timeline_df.iloc[-1]
        y = pdf.get_y()
        pdf_kpi_card(pdf, 10, y, "Avances cumulées", f"{last_row['Avances cumulées']:.2f} DT", BRAND_TEAL, width=58)
        pdf_kpi_card(pdf, 76, y, "Paiements engagés", f"{last_row['Paiements engagés cumulés']:.2f} DT", (41, 137, 202), width=58)
        balance_accent = BRAND_TEAL if last_row["Solde financement"] >= 0 else (200, 72, 72)
        balance_label = "Excédent financement" if last_row["Solde financement"] >= 0 else "Besoin financement"
        pdf_kpi_card(pdf, 142, y, balance_label, f"{abs(last_row['Solde financement']):.2f} DT", balance_accent, width=58)
        pdf.set_y(y + 28)
        pdf.set_text_color(*BRAND_NAVY)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, safe_text("Détails chronologiques"), ln=True)
        headers = ["Date", "Evénement", "Montant", "Avances cumulées", "Paiements cumulés", "Solde"]
        widths = [30, 34, 28, 34, 34, 30]
        pdf.set_fill_color(*BRAND_NAVY)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 7)
        for header, width in zip(headers, widths):
            pdf.cell(width, 8, safe_text(header), 1, 0, "C", True)
        pdf.ln()
        pdf.set_text_color(*BRAND_NAVY)
        pdf.set_font("Arial", '', 7)
        for _, row in timeline_df.iterrows():
            if pdf.get_y() > 260:
                pdf_footer(pdf)
                pdf.add_page()
                add_pdf_header(pdf, "Rapport financement", selected_client, selected_project)
            data = [
                row["Date"].strftime("%d/%m/%Y %H:%M"),
                row["Evénement"],
                f"{row['Montant événement']:.2f}",
                f"{row['Avances cumulées']:.2f}",
                f"{row['Paiements engagés cumulés']:.2f}",
                f"{row['Solde financement']:.2f}",
            ]
            for item, width in zip(data, widths):
                pdf.cell(width, 7, safe_text(item), 1)
            pdf.ln()
    pdf_footer(pdf)
    output = BytesIO()
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_pdf.close()
    pdf.output(dest='F', name=temp_pdf.name)
    with open(temp_pdf.name, 'rb') as f:
        output.write(f.read())
    output.seek(0)
    os.remove(temp_pdf.name)
    return output

def render_financing_timeline(cursor, project_id, selected_client="", selected_project=""):
    timeline_df = build_financing_timeline(cursor, project_id)
    st.markdown("<div class='card'><h2>Récap financement : avances vs paiements engagés</h2>", unsafe_allow_html=True)
    if timeline_df.empty:
        st.info("Aucune avance ou historique de paiement n'est encore disponible pour établir le récapitulatif.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    last_row = timeline_df.iloc[-1]
    max_value = max(
        float(last_row["Avances cumulées"]),
        float(last_row["Paiements engagés cumulés"]),
        1,
    )
    advance_pct = max(2, min(100, float(last_row["Avances cumulées"]) / max_value * 100))
    payment_pct = max(2, min(100, float(last_row["Paiements engagés cumulés"]) / max_value * 100))
    balance_class = "positive" if last_row["Solde financement"] >= 0 else "negative"
    balance_label = "Excédent de financement" if last_row["Solde financement"] >= 0 else "Besoin de financement"
    summary_html = (
        "<div class='finance-summary-panel'>"
        "<div class='finance-summary-bars'>"
        "<div class='finance-summary-line'>"
        "<div class='finance-summary-label'>Avances cumulées</div>"
        f"<div class='finance-bar'><div class='finance-fill advance' style='width:{advance_pct:.1f}%'></div></div>"
        f"<div class='finance-summary-value'>{last_row['Avances cumulées']:.2f} DT</div>"
        "</div>"
        "<div class='finance-summary-line'>"
        "<div class='finance-summary-label'>Paiements engagés</div>"
        f"<div class='finance-bar'><div class='finance-fill payment' style='width:{payment_pct:.1f}%'></div></div>"
        f"<div class='finance-summary-value'>{last_row['Paiements engagés cumulés']:.2f} DT</div>"
        "</div>"
        "</div>"
        f"<div class='finance-summary-status {balance_class}'><div>{balance_label}<strong>{abs(last_row['Solde financement']):.2f} DT</strong></div></div>"
        "</div>"
    )
    st.markdown(summary_html, unsafe_allow_html=True)
    pdf_bytes = generate_financing_pdf(timeline_df, selected_client, selected_project)
    st.download_button(
        "📊 Télécharger le rapport financement PDF",
        data=pdf_bytes,
        file_name=f"rapport_financement_{selected_client}_{selected_project}.pdf",
        mime="application/pdf"
    )
    st.markdown("</div>", unsafe_allow_html=True)

def add_pdf_header(pdf, title, selected_client="", selected_project=""):
    pdf.set_fill_color(*BRAND_NAVY)
    pdf.rect(0, 0, 210, 34, "F")
    pdf.set_fill_color(*BRAND_TEAL)
    pdf.rect(156, 0, 54, 34, "F")
    pdf.set_draw_color(255, 255, 255)
    pdf.set_line_width(2)
    pdf.line(150, 0, 132, 34)
    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, x=10, y=6, w=28)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 18)
    pdf.text(42, 15, "MHD")
    pdf.set_font("Arial", '', 9)
    pdf.text(42, 22, safe_text("CABINET D'ARCHITECTURE"))
    pdf.text(42, 28, safe_text("MOURAD HAMMAMI"))
    pdf.set_text_color(*BRAND_NAVY)
    pdf.set_font("Arial", 'B', 22)
    pdf.set_xy(10, 47)
    pdf.cell(0, 10, safe_text(title.upper()), ln=True)
    pdf.set_draw_color(*BRAND_GOLD)
    pdf.set_line_width(1)
    pdf.line(10, 62, 42, 62)
    pdf.ln(10)
    draw_pdf_info_cards(pdf, selected_client, selected_project)

def draw_pdf_info_cards(pdf, selected_client="", selected_project=""):
    pdf.set_y(72)
    cards = [
        ("DATE", datetime.today().strftime('%d/%m/%Y')),
        ("CLIENT", selected_client or "-"),
        ("PROJET", selected_project or "-"),
    ]
    card_w = 60
    x = 10
    for label, value in cards:
        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(224, 230, 233)
        pdf.rect(x, 72, card_w, 18, "DF")
        pdf.set_font("Arial", 'B', 8)
        pdf.set_text_color(*BRAND_NAVY)
        pdf.text(x + 5, 79, safe_text(label))
        pdf.set_font("Arial", '', 10)
        pdf.text(x + 5, 86, safe_text(value)[:28])
        x += card_w + 4
    pdf.set_y(100)

def pdf_footer(pdf):
    y = 276
    pdf.set_fill_color(242, 246, 246)
    pdf.rect(10, y, 190, 15, "F")
    pdf.set_draw_color(*BRAND_TEAL)
    pdf.line(10, y, 200, y)
    pdf.set_text_color(*BRAND_NAVY)
    pdf.set_font("Arial", '', 8)
    pdf.text(14, y + 9, safe_text("Concevoir aujourd'hui, construire demain."))
    pdf.text(88, y + 9, safe_text("+216 55 555 555  |  contact@mhd-architecture.tn"))
    pdf.text(166, y + 9, safe_text("Tunis, Tunisie"))

def pdf_kpi_card(pdf, x, y, label, value, accent=BRAND_TEAL, width=58):
    pdf.set_fill_color(255, 255, 255)
    pdf.set_draw_color(224, 230, 233)
    pdf.rect(x, y, width, 20, "DF")
    pdf.set_text_color(*BRAND_NAVY)
    pdf.set_font("Arial", 'B', 7)
    pdf.text(x + 5, y + 7, safe_text(label.upper()))
    pdf.set_text_color(*accent)
    pdf.set_font("Arial", 'B', 13)
    pdf.text(x + 5, y + 16, safe_text(value))

def create_progress_ring_image(percent, accent=BRAND_TEAL):
    percent = max(0, min(100, int(percent or 0)))
    size = 180
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    box = (14, 14, size - 14, size - 14)
    draw.ellipse(box, outline=(229, 230, 232, 255), width=16)
    if percent > 0:
        draw.arc(box, start=-90, end=-90 + int(360 * percent / 100), fill=accent + (255,), width=16)
    draw.ellipse((36, 36, size - 36, size - 36), fill=(255, 255, 255, 255))
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    temp.close()
    img.save(temp.name)
    return temp.name

def create_pdf_photo_image(encoded_image):
    if not encoded_image:
        return None
    try:
        data = base64.b64decode(encoded_image)
        src = Image.open(BytesIO(data)).convert("RGB")
        src.thumbnail((260, 180))
        canvas = Image.new("RGB", (260, 180), (244, 245, 246))
        x = (260 - src.width) // 2
        y = (180 - src.height) // 2
        canvas.paste(src, (x, y))
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp.close()
        canvas.save(temp.name, quality=88)
        return temp.name
    except Exception:
        return None

def render_tracking_report_html(df, total_cout, total_paiement, current_advance, besoin_financement, taux_moyen):
    accents = ["#139186", "#2989ca", "#f28e2b"]
    rows_html = []
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        accent = accents[(idx - 1) % len(accents)]
        image_html = "<div class='tracking-placeholder'>Aucune</div>"
        if row.get("Image"):
            image_html = f"<img class='tracking-photo' src='data:image/png;base64,{row['Image']}' alt='photo chantier'>"
        percent = max(0, min(100, int(row.get("Avancement (%)", 0) or 0)))
        rows_html.append(
            "<div class='tracking-row'>"
            f"<div class='tracking-cell tracking-lot' style='background:{accent}'><div>{idx:02d}</div><small>{html.escape(str(row['Lot']))[:16]}</small></div>"
            f"<div class='tracking-cell tracking-designation'><strong>{html.escape(str(row['Lot']))}</strong><span>{html.escape(str(row['Désignation']))}</span></div>"
            f"<div class='tracking-cell'>{float(row['Quantité']):.2f}</div>"
            f"<div class='tracking-cell'>{html.escape(str(row['Unité']))}</div>"
            f"<div class='tracking-cell'>{float(row['Prix Unitaire']):.2f}</div>"
            f"<div class='tracking-cell tracking-total'>{float(row['Coût Total']):.2f} DT</div>"
            f"<div class='tracking-cell'><div class='tracking-ring' style='--pct:{percent}; --accent:{accent};'><span>{percent}%</span></div></div>"
            f"<div class='tracking-cell'>{image_html}</div>"
            "</div>"
        )
    if besoin_financement < 0:
        finance_label = "Besoin de financement"
        finance_value = f"{-besoin_financement:.2f} DT"
    else:
        finance_label = "Excédent de financement"
        finance_value = f"{besoin_financement:.2f} DT"
    report_html = (
        "<div class='tracking-report'>"
        "<div class='tracking-header'>"
        "<div class='tracking-cell'>Lot</div>"
        "<div class='tracking-cell'>Désignation</div>"
        "<div class='tracking-cell'>Qté</div>"
        "<div class='tracking-cell'>Unité</div>"
        "<div class='tracking-cell'>PU (DT)</div>"
        "<div class='tracking-cell'>Total (DT)</div>"
        "<div class='tracking-cell'>% Avancement</div>"
        "<div class='tracking-cell'>Image</div>"
        "</div>"
        f"{''.join(rows_html)}"
        "</div>"
        "<div class='report-kpis'>"
        f"<div class='design-kpi report-kpi-main'><div class='report-kpi-icon'>DT</div><div><small>Total devis TTC</small><strong>{total_cout:.2f} DT</strong></div></div>"
        f"<div class='design-kpi'><small>Paiement engagé</small><strong>{total_paiement:.2f} DT</strong></div>"
        f"<div class='design-kpi'><small>Avance perçue</small><strong>{current_advance:.2f} DT</strong></div>"
        f"<div class='design-kpi'><small>{finance_label}</small><strong>{finance_value}</strong></div>"
        f"<div class='design-kpi'><small>Taux moyen réalisation</small><strong>{taux_moyen:.2f}%</strong></div>"
        "</div>"
    )
    st.markdown(report_html, unsafe_allow_html=True)

def draw_project_pdf_table(pdf, df, include_tracking=False, temp_assets=None):
    if temp_assets is None:
        temp_assets = []
    headers = ["LOT", "DESIGNATION", "QTE", "UNITE", "PU (DT)", "TOTAL (DT)"]
    widths = [16, 62, 18, 18, 22, 28]
    if include_tracking:
        widths = [14, 50, 16, 16, 19, 25]
        headers += ["% AV.", "IMAGE"]
        widths += [25, 25]
    pdf.set_fill_color(*BRAND_NAVY)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 8)
    for header, width in zip(headers, widths):
        pdf.cell(width, 9, safe_text(header), 1, 0, "C", True)
    pdf.ln()
    accents = [BRAND_TEAL, (41, 137, 202), (242, 142, 43)]
    pdf.set_font("Arial", '', 8)
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        if pdf.get_y() > 247:
            pdf_footer(pdf)
            pdf.add_page()
            add_pdf_header(pdf, "Suite du document")
            pdf.set_fill_color(*BRAND_NAVY)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", 'B', 8)
            for header, width in zip(headers, widths):
                pdf.cell(width, 9, safe_text(header), 1, 0, "C", True)
            pdf.ln()
            pdf.set_font("Arial", '', 8)
        accent = accents[(idx - 1) % len(accents)]
        pdf.set_fill_color(*accent)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(widths[0], 18, f"{idx:02d}", 1, 0, "C", True)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(*BRAND_NAVY)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(widths[1], 18, safe_text(f"{row['Lot']} - {row['Désignation']}")[:39], 1)
        pdf.set_font("Arial", '', 8)
        pdf.cell(widths[2], 18, safe_text(row['Quantité']), 1, 0, "C")
        pdf.cell(widths[3], 18, safe_text(row['Unité']), 1, 0, "C")
        pdf.cell(widths[4], 18, f"{row['Prix Unitaire']:.2f}", 1, 0, "R")
        pdf.set_text_color(*BRAND_TEAL)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(widths[5], 18, f"{row['Coût Total']:.2f}", 1, 0, "R")
        if include_tracking:
            x_ring = pdf.get_x()
            y_ring = pdf.get_y()
            pdf.cell(widths[6], 18, "", 1)
            ring_path = create_progress_ring_image(row["Avancement (%)"], accent)
            temp_assets.append(ring_path)
            pdf.image(ring_path, x=x_ring + 5, y=y_ring + 2.5, w=14, h=14)
            pdf.set_text_color(*BRAND_NAVY)
            pdf.set_font("Arial", 'B', 7)
            pdf.text(x_ring + 10, y_ring + 11, f"{int(row['Avancement (%)'])}%")
            x_img = pdf.get_x()
            y_img = pdf.get_y()
            pdf.cell(widths[7], 18, "", 1)
            photo_path = create_pdf_photo_image(row.get("Image"))
            if photo_path:
                temp_assets.append(photo_path)
                pdf.image(photo_path, x=x_img + 2, y=y_img + 2, w=24, h=14)
            else:
                pdf.set_text_color(120, 132, 140)
                pdf.set_font("Arial", '', 7)
                pdf.text(x_img + 7, y_img + 10, "Aucune")
        pdf.ln()
    return temp_assets

def render_logo(width=190):
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=width)

def image_data_uri(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    ext = os.path.splitext(path)[1].lower().replace(".", "") or "png"
    if ext == "jpg":
        ext = "jpeg"
    return f"data:image/{ext};base64,{encoded}"

def render_app_header(title, subtitle, mode_label):
    logo_src = image_data_uri(LOGO_PATH)
    hero_src = image_data_uri(HERO_IMAGE_PATH)
    logo_html = f"<img class='mhd-hero-logo' src='{logo_src}' alt='MHD'>" if logo_src else ""
    hero_img_html = f"<img class='mhd-hero-photo' src='{hero_src}' alt='Création architecturale moderne'>" if hero_src else ""
    st.markdown(
        f"""
        <div class="mhd-version-badge">MHD DESIGN 2026</div>
        <section class="mhd-hero">
            {hero_img_html}
            <div class="mhd-hero-top">
                <div class="mhd-hero-brand">
                    <div class="mhd-hero-brand-row">
                        {logo_html}
                        <div>
                            <div class="mhd-brand-name">MHD</div>
                            <div class="mhd-brand-subtitle">Cabinet d'architecture</div>
                            <div class="mhd-brand-person">Mourad Hammami</div>
                        </div>
                    </div>
                </div>
                <div class="mhd-villa-scene" aria-hidden="true">
                    <div class="mhd-villa">
                        <span class="mhd-window one"></span>
                        <span class="mhd-window two"></span>
                        <span class="mhd-window three"></span>
                    </div>
                </div>
            </div>
            <div class="mhd-hero-title">
                <div class="mhd-mode-badge">{html.escape(mode_label)}</div>
                <h1>{html.escape(title)}</h1>
                <strong>{html.escape(subtitle)}</strong>
                <div class="mhd-gold-line"></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True
    )

def render_client_progress_bar(label, percent, amount_text):
    percent = max(0, min(100, int(percent or 0)))
    st.markdown(
        f"""
        <div class="client-progress-row">
            <div class="client-progress-head">
                <strong>{label}</strong>
                <span>{percent}% · {amount_text}</span>
            </div>
            <div class="client-progress-track">
                <div class="client-progress-fill" style="width:{percent}%"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_client_portal(conn):
    c = conn.cursor()
    render_app_header("Espace client", "Suivi des travaux", "Client")

    if "client_portal_user" not in st.session_state:
        st.session_state.client_portal_user = None

    if not st.session_state.client_portal_user:
        login_col, intro_col = st.columns([1, 1.4])
        with login_col:
            st.markdown("<div class='card'><h2>Connexion client</h2>", unsafe_allow_html=True)
            username = st.text_input("Identifiant")
            password = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                c.execute('''
                    SELECT u.client_id, c.client_name
                    FROM client_portal_users u
                    JOIN clients c ON c.client_id = u.client_id
                    WHERE u.username = ? AND u.password_hash = ?
                ''', (username.strip(), password_hash(password)))
                user = c.fetchone()
                if user:
                    st.session_state.client_portal_user = {"client_id": user[0], "client_name": user[1]}
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
            st.markdown("</div>", unsafe_allow_html=True)
        with intro_col:
            st.markdown(
                """
                <div class='card client-summary'>
                    <h2>Votre tableau de bord</h2>
                    <p>Consultez les avances perçues, l'amortissement du budget par lot, les photos de visite et l'état d'avancement global du chantier.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
        return

    client = st.session_state.client_portal_user
    top_left, top_right = st.columns([3, 1])
    top_left.markdown(f"<h2>Bonjour {client['client_name']}</h2>", unsafe_allow_html=True)
    if top_right.button("Déconnexion"):
        st.session_state.client_portal_user = None
        st.rerun()

    c.execute("SELECT project_id, project_name FROM projects WHERE client_id = ? AND project_status = 'suivi' ORDER BY created_at DESC", (client["client_id"],))
    projects = c.fetchall()
    if not projects:
        st.info("Aucun projet validé n'est encore disponible dans votre espace client.")
        return

    project_options = {row[1]: row[0] for row in projects}
    selected_project = st.selectbox("Projet", options=list(project_options.keys()))
    project_id = project_options[selected_project]

    current_advance = get_total_advances(c, project_id)

    c.execute('''
        SELECT lot, designation, unite, quantite, prix_unitaire, cout_total, avancement, paiement, image, updated_at
        FROM project_details
        WHERE project_id = ?
        ORDER BY lot, designation
    ''', (project_id,))
    rows = c.fetchall()
    if not rows:
        st.info("Le devis global existe peut-être encore en préparation. Aucun avancement n'a été publié pour ce projet.")
        return

    df_client = pd.DataFrame(rows, columns=["Lot", "Désignation", "Unité", "Quantité", "Prix Unitaire", "Coût Total", "Avancement (%)", "Paiement Engagé", "Image", "Date"])
    df_client["Budget"] = df_client["Coût Total"].fillna(0)
    df_client["Amortissement"] = df_client["Paiement Engagé"].fillna(0)
    df_client["Avancement"] = df_client["Avancement (%)"].fillna(0)
    df_client["Budget"] = df_client["Budget"].fillna(0)
    df_client["Avancement"] = df_client["Avancement"].fillna(0)
    df_client["Amortissement"] = df_client["Amortissement"].fillna(0)
    total_budget = df_client["Budget"].sum()
    total_amort = df_client["Amortissement"].sum()
    global_rate = (total_amort / total_budget * 100) if total_budget else 0
    remaining_advance = current_advance - total_amort

    st.markdown("<div class='card'><h2>Devis global et suivi d'avancement</h2>", unsafe_allow_html=True)
    render_tracking_report_html(
        df_client,
        total_budget,
        total_amort,
        current_advance,
        remaining_advance,
        global_rate
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Initialisation de l'état de la session
if "lots_db" not in st.session_state:
    # Charger les lots prédéfinis à partir du contenu du fichier fourni
    predefined_data = [
        {"lots": "Démolition", "DESIGNATIONS": "Mur double cloison et cloison de 10cm"},
        {"lots": "Démolition", "DESIGNATIONS": "Démolition, tuyauteries; sanitaire et radiateurs"},
        {"lots": "Terrasse", "DESIGNATIONS": "Terrasse au RDC chappe et pose granito blanc"},
        {"lots": "Terrasse", "DESIGNATIONS": "suite a l'existant (20x40)"},
        {"lots": "Béton extention + Plancher", "DESIGNATIONS": "Béton armé en élevation"},
        {"lots": "Béton extention + Plancher", "DESIGNATIONS": "Plancher (16 + 5)"},
        {"lots": "Maçonneries extention", "DESIGNATIONS": "Double cloison de 0,30"},
        {"lots": "Maçonneries extention", "DESIGNATIONS": "Mur de 15 cm pour cloture"},
        {"lots": "Maçonneries extention", "DESIGNATIONS": "Cloison de 10 cm en placo platre avec isolation"},
        {"lots": "Enduits - Ravelements", "DESIGNATIONS": "Enduit intérieur"},
        {"lots": "Enduits - Ravelements", "DESIGNATIONS": "Enduit extérieur"},
        {"lots": "Enduits - Ravelements", "DESIGNATIONS": "Enduit sous plafond"},
        {"lots": "Revêtements", "DESIGNATIONS": "F.Pose en carreaux effet marbre blanc 20x40 extention"},
        {"lots": "Revêtements", "DESIGNATIONS": "F.Pose de carreaux en grès"},
        {"lots": "Revêtements", "DESIGNATIONS": "F. Pose de revêtement muraux en faïence"},
        {"lots": "Revêtements", "DESIGNATIONS": "F.Pose d'appuis de fenêtre"},
        {"lots": "Revêtements", "DESIGNATIONS": "F.Pose de dalle en marbre pour plage lavabo"},
        {"lots": "Ouvrages divers", "DESIGNATIONS": "F.Pose de pipette en PVC"},
        {"lots": "Ouvrages divers", "DESIGNATIONS": "F.Pose plage lavabo en ceramique"},
        {"lots": "Ouvrages divers", "DESIGNATIONS": "F.Pde Pissotieres avec boutton poussoire"},
        {"lots": "Ouvrages divers", "DESIGNATIONS": "F. P de cuvette (Sanimed)"},
        {"lots": "Ouvrages divers", "DESIGNATIONS": "F,P Robinet chaud et froid"},
        {"lots": "Ouvrages divers", "DESIGNATIONS": "F.Pose flexible de toilette"},
        {"lots": "Ouvrages divers", "DESIGNATIONS": "Réservation d'extracteur buée"},
        {"lots": "Ouvrages divers", "DESIGNATIONS": "Souche de gaine technique"},
        {"lots": "Forme de Pente + étanchéité", "DESIGNATIONS": "Forme de pente"},
        {"lots": "Forme de Pente + étanchéité", "DESIGNATIONS": "Enduit de ravoirage"},
        {"lots": "Forme de Pente + étanchéité", "DESIGNATIONS": "Etancheité sur terrasse"},
        {"lots": "Forme de Pente + étanchéité", "DESIGNATIONS": "Relevé d'étancheité"},
        {"lots": "Forme de Pente + étanchéité", "DESIGNATIONS": "Auto protection"},
        {"lots": "Reseaux diver + Regards", "DESIGNATIONS": "F. transport et pose de canalisation"},
        {"lots": "Reseaux diver + Regards", "DESIGNATIONS": "a) conduite en PVC O 100"},
        {"lots": "Reseaux diver + Regards", "DESIGNATIONS": "b) conduite en PVC O 140"},
        {"lots": "Reseaux diver + Regards", "DESIGNATIONS": "c) conduite en PVC O 150"},
        {"lots": "Reseaux diver + Regards", "DESIGNATIONS": "Regards"},
        {"lots": "Reseaux diver + Regards", "DESIGNATIONS": "a) regards 40 x 40"},
        {"lots": "Reseaux diver + Regards", "DESIGNATIONS": "b) regards 60 x 60"},
        {"lots": "Peintures", "DESIGNATIONS": "Peinture extérieure"},
        {"lots": "Peintures", "DESIGNATIONS": "Peinture intérieure"},
        {"lots": "Peintures", "DESIGNATIONS": "Peinture laquée"},
        {"lots": "Peintures", "DESIGNATIONS": "Peinture sur boiseries"},
        {"lots": "Peintures", "DESIGNATIONS": "Peinture sur ferronnerie"},
        {"lots": "Divers", "DESIGNATIONS": "Menuiserie aluminium +boxe toilette Forfait"},
        {"lots": "Divers", "DESIGNATIONS": "FP Electricite Forfait"},
        {"lots": "Divers", "DESIGNATIONS": "FP tuyautterie pour chauffage central plomberie Forfait"},
        {"lots": "Divers", "DESIGNATIONS": "Menuiserie entretient et quincaillerie Forfait"},
        {"lots": "test mourad", "DESIGNATIONS": "t1"},
        {"lots": "test mourad", "DESIGNATIONS": "t2"},
        {"lots": "test mourad", "DESIGNATIONS": "t3"},
        {"lots": "test mourad", "DESIGNATIONS": "t4"}
    ]
    df_predefined = pd.DataFrame(predefined_data)
    
    # Charger le fichier utilisateur s'il existe
    uploaded_lot_file = "lot et designation par lot.xlsx"
    if os.path.exists(uploaded_lot_file):
        df_user = pd.read_excel(uploaded_lot_file)
        df_user.columns = df_user.columns.str.strip()
        df_user["lots"] = df_user["lots"].astype(str).str.strip()
        df_user["DESIGNATIONS"] = df_user["DESIGNATIONS"].astype(str).str.strip()
    else:
        df_user = pd.DataFrame(columns=["lots", "DESIGNATIONS"])

    # Charger les lots précédemment enregistrés s'ils existent
    if os.path.exists("lot_et_designation_par_lot.xlsx"):
        df_previous = pd.read_excel("lot_et_designation_par_lot.xlsx")
        df_previous.columns = df_previous.columns.str.strip()
        df_previous["lots"] = df_previous["lots"].astype(str).str.strip()
        df_previous["DESIGNATIONS"] = df_previous["DESIGNATIONS"].astype(str).str.strip()
    else:
        df_previous = pd.DataFrame(columns=["lots", "DESIGNATIONS"])

    # Combiner toutes les données
    df_combined = pd.concat([df_predefined, df_user, df_previous], ignore_index=True)
    df_combined.drop_duplicates(subset=["lots", "DESIGNATIONS"], inplace=True)
    st.session_state.lots_db = df_combined.copy()

if "devis_data" not in st.session_state:
    st.session_state.devis_data = []

if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = {}

if "scanned_quote_rows" not in st.session_state:
    st.session_state.scanned_quote_rows = {}

def get_secret_value(name):
    try:
        return st.secrets[name]
    except Exception:
        return os.environ.get(name, "")

def get_query_param(name, default=""):
    try:
        value = st.query_params.get(name, default)
    except Exception:
        return default
    if isinstance(value, list):
        return value[0] if value else default
    return value or default

def is_client_portal_link():
    espace = str(get_query_param("espace", "")).strip().lower()
    return espace in ["client", "espace-client", "espace_client"]

def get_client_portal_link():
    public_app_url = str(get_secret_value("PUBLIC_APP_URL")).strip().rstrip("/")
    if public_app_url:
        return f"{public_app_url}?espace=client"
    return "?espace=client"

def require_architect_login():
    if "architect_logged_in" not in st.session_state:
        st.session_state.architect_logged_in = False

    if st.session_state.architect_logged_in:
        with st.sidebar:
            st.success("Architecte connecté")
            if st.button("Déconnexion architecte"):
                st.session_state.architect_logged_in = False
                st.rerun()
        return True

    expected_username = str(get_secret_value("ARCHITECT_USERNAME"))
    expected_password = str(get_secret_value("ARCHITECT_PASSWORD"))

    st.markdown("<div class='card'><h2>Connexion architecte</h2>", unsafe_allow_html=True)
    username = st.text_input("Identifiant architecte")
    password = st.text_input("Mot de passe architecte", type="password")

    if not expected_username or not expected_password:
        st.warning("Configurez ARCHITECT_USERNAME et ARCHITECT_PASSWORD dans les secrets Streamlit avant la mise en ligne.")

    if st.button("Se connecter", key="architect_login"):
        valid_user = hmac.compare_digest(username.strip(), expected_username)
        valid_password = hmac.compare_digest(password, expected_password)

        if expected_username and expected_password and valid_user and valid_password:
            st.session_state.architect_logged_in = True
            st.rerun()
        else:
            st.error("Identifiant ou mot de passe architecte incorrect.")

    st.markdown("</div>", unsafe_allow_html=True)
    return False

conn = db_connect()
c = conn.cursor()

if is_client_portal_link():
    app_mode = "Espace client"
else:
    app_mode = st.sidebar.radio("Accès", ["Architecte", "Espace client"], horizontal=False)

if app_mode == "Espace client":
    render_client_portal(conn)
    conn.close()
    st.stop()

# Titre avec logo
render_app_header("Devis global", "Et suivi d'avancement", "Architecte")

if not require_architect_login():
    conn.close()
    st.stop()

# Gestion des clients et projets
st.markdown("<div class='card'><h2>👤 Gestion des Clients et Projets</h2>", unsafe_allow_html=True)

# Sélection ou création d'un client
client_name = st.text_input("Nom du client", placeholder="Ex: Jean Dupont")
if client_name:
    c.execute("INSERT OR IGNORE INTO clients (client_name) VALUES (?)", (client_name,))
    conn.commit()

c.execute("SELECT client_id, client_name FROM clients")
clients = c.fetchall()
client_options = {row[1]: row[0] for row in clients}
selected_client = st.selectbox("Sélectionner un client", options=[""] + list(client_options.keys()))
client_id = client_options.get(selected_client) if selected_client else None

# Sélection ou création d'un projet
project_id = None
project_status = "devis_initial"
deadline_alerts_enabled = False
if client_id:
    with st.expander("🔐 Accès client au suivi des travaux"):
        client_portal_link = get_client_portal_link()
        st.markdown("**Lien interface client**")
        st.code(client_portal_link, language=None)
        st.caption("Envoyez ce lien au client avec son identifiant et son mot de passe.")
        c.execute("SELECT username, updated_at FROM client_portal_users WHERE client_id = ?", (client_id,))
        existing_access = c.fetchone()
        if existing_access:
            st.info(f"Accès actif : {existing_access[0]} · modifié le {format_date(existing_access[1])}")
        portal_username = st.text_input("Identifiant client", value=existing_access[0] if existing_access else selected_client.lower().replace(" ", "."))
        portal_password = st.text_input("Mot de passe client", type="password", help="À transmettre au client pour consulter son tableau de bord.")
        if st.button("Enregistrer l'accès client"):
            if portal_username.strip() and portal_password:
                c.execute('''
                    INSERT INTO client_portal_users (client_id, username, password_hash, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(client_id) DO UPDATE SET
                        username = excluded.username,
                        password_hash = excluded.password_hash,
                        updated_at = excluded.updated_at
                ''', (client_id, portal_username.strip(), password_hash(portal_password), datetime.now().isoformat()))
                conn.commit()
                st.success("Accès client enregistré.")
            else:
                st.error("Veuillez renseigner un identifiant et un mot de passe.")

    project_name = st.text_input("Nom du projet", placeholder="Ex: Rénovation Villa")
    if project_name and st.button("Créer nouveau projet"):
        c.execute("INSERT INTO projects (client_id, project_name, created_at, project_status) VALUES (?, ?, ?, ?)",
                  (client_id, project_name, datetime.now().isoformat(), "devis_initial"))
        conn.commit()
        st.success(f"Projet « {project_name} » créé pour « {selected_client} »")

    c.execute("SELECT project_id, project_name FROM projects WHERE client_id = ?", (client_id,))
    projects = c.fetchall()
    project_options = {row[1]: row[0] for row in projects}
    selected_project = st.selectbox("Sélectionner un projet", options=[""] + list(project_options.keys()))
    project_id = project_options.get(selected_project) if selected_project else None
    project_status = "devis_initial"
    if project_id:
        c.execute("SELECT project_status, deadline_alerts_enabled FROM projects WHERE project_id = ?", (project_id,))
        status_row = c.fetchone()
        project_status = status_row[0] if status_row and status_row[0] else "devis_initial"
        deadline_alerts_enabled = bool(status_row[1]) if status_row and len(status_row) > 1 else False
        status_label = "Devis initial à valider" if project_status != "suivi" else "Suivi de réalisation"
        st.markdown(f"<span class='stage-pill'>{status_label}</span>", unsafe_allow_html=True)
        if project_status == "suivi":
            new_deadline_alerts_enabled = st.checkbox(
                "Activer les alertes et la barre de délai des lots",
                value=deadline_alerts_enabled,
                help="Visible uniquement dans l'environnement architecte. Alerte si le délai est dépassé ou s'il reste 2 jours avec un avancement inférieur à 50%."
            )
            if new_deadline_alerts_enabled != deadline_alerts_enabled:
                c.execute(
                    "UPDATE projects SET deadline_alerts_enabled = ? WHERE project_id = ?",
                    (1 if new_deadline_alerts_enabled else 0, project_id)
                )
                conn.commit()
                deadline_alerts_enabled = new_deadline_alerts_enabled

    # Saisie et historique des avances perçues
    if project_id:
        # Bouton pour supprimer le projet
        if st.button("🗑️ Supprimer le projet", key="delete_project"):
            c.execute("DELETE FROM project_details WHERE project_id = ?", (project_id,))
            c.execute("DELETE FROM project_history WHERE project_id = ?", (project_id,))
            c.execute("DELETE FROM project_advances WHERE project_id = ?", (project_id,))
            c.execute("DELETE FROM projects WHERE project_id = ?", (project_id,))
            conn.commit()
            st.success(f"Projet « {selected_project} » supprimé avec succès !")
            st.rerun()

    if project_id and project_status == "suivi":
        project_total_for_advances = get_project_total(c, project_id)
        total_advances = get_total_advances(c, project_id)
        remaining_advance_capacity = max(0.0, project_total_for_advances - total_advances)
        st.markdown("<h3>💰 Avances perçues</h3>", unsafe_allow_html=True)
        col_total, col_remaining = st.columns(2)
        col_total.metric("Total avances", f"{total_advances:.2f} DT")
        col_remaining.metric("Reste possible", f"{remaining_advance_capacity:.2f} DT")
        if project_total_for_advances <= 0:
            st.info("Enregistrez d'abord le devis validé pour définir le montant global avant d'ajouter une avance.")
        elif remaining_advance_capacity <= 0:
            st.success("Le total des avances atteint déjà le montant global du devis.")
        else:
            advance_amount = st.number_input(
                "Nouvelle avance perçue (DT)",
                min_value=0.0,
                max_value=float(remaining_advance_capacity),
                step=100.0,
                value=0.0,
                help="Le total des avances ne peut pas dépasser le montant global du devis."
            )
            if st.button("Ajouter cette avance"):
                if advance_amount <= 0:
                    st.error("Veuillez saisir une avance supérieure à 0 DT.")
                elif total_advances + advance_amount > project_total_for_advances:
                    st.error("Cette avance dépasse le montant global du devis.")
                else:
                    c.execute("INSERT INTO project_advances (project_id, advance_amount, updated_at) VALUES (?, ?, ?)",
                              (project_id, advance_amount, datetime.now().isoformat()))
                    conn.commit()
                    st.success(f"Avance de {advance_amount:.2f} DT ajoutée pour « {selected_project} »")
                    st.rerun()

        # Afficher l'historique des avances avec option de suppression
        c.execute("SELECT advance_id, advance_amount, updated_at FROM project_advances WHERE project_id = ? ORDER BY updated_at ASC", (project_id,))
        advances = c.fetchall()
        if advances:
            advances_df = pd.DataFrame(advances, columns=["ID", "Montant Avance (DT)", "Mis à jour le"])
            with st.expander("Voir l'historique des avances"):
                st.markdown("**Historique des avances perçues**")
                for i, row in advances_df.iterrows():
                    cols = st.columns([2, 3, 3, 2])
                    cols[0].write(f"Avance {i + 1}")
                    cols[1].write(f"{row['Montant Avance (DT)']:.2f} DT")
                    cols[2].write(format_date(row["Mis à jour le"]))
                    if cols[3].button("🗑️", key=f"delete_advance_{row['ID']}", help="Supprimer cette avance"):
                        c.execute("DELETE FROM project_advances WHERE advance_id = ?", (row["ID"],))
                        conn.commit()
                        st.success(f"Avance de {row['Montant Avance (DT)']:.2f} DT supprimée !")
                        st.rerun()
        else:
            st.info("Aucun historique d'avances disponible pour ce projet.")

        # Afficher l'historique du projet avec option de suppression
        st.markdown("<h3>📜 Historique des paiements engagés</h3>", unsafe_allow_html=True)
        c.execute("SELECT history_id, lot, designation, avancement, paiement, image, updated_at FROM project_history WHERE project_id = ? ORDER BY updated_at DESC", (project_id,))
        history = c.fetchall()
        if history:
            history_df = pd.DataFrame(history, columns=["ID", "Lot", "Désignation", "Avancement (%)", "Paiement Engagé (DT)", "Image", "Mis à jour le"])
            with st.expander("Voir l'historique des paiements"):
                st.markdown("**Historique des paiements engagés**")
                for i, row in history_df.iterrows():
                    cols = st.columns([2, 3, 2, 2, 2])
                    cols[0].write(row["Lot"])
                    cols[1].write(row["Désignation"])
                    cols[2].write(f"{row['Avancement (%)']}%")
                    cols[3].write(f"{row['Paiement Engagé (DT)'] or 0:.2f} DT")
                    if cols[4].button("🗑️", key=f"delete_history_{row['ID']}", help="Supprimer cet historique"):
                        c.execute("DELETE FROM project_history WHERE history_id = ?", (row["ID"],))
                        conn.commit()
                        st.success(f"Historique pour {row['Désignation']} supprimé !")
                        st.rerun()
                for _, row in history_df.iterrows():
                    if row["Image"]:
                        st.image(base64.b64decode(row["Image"]), width=200, caption=f"{row['Lot']} - {row['Désignation']} ({row['Mis à jour le']})")
        else:
            st.info("Aucun historique de paiements disponible pour ce projet.")
        render_financing_timeline(c, project_id, selected_client, selected_project)
    elif project_id:
        st.info("Ce projet est encore au stade devis initial : aucune avance, photo ou visite chantier n'est demandée avant validation du devis.")

# Bouton de réinitialisation
if st.button("🔄 Nouveau devis"):
    st.session_state.devis_data = []
    st.session_state.uploaded_images = {}
    if os.path.exists("lot et designation par lot.xlsx"):
        os.remove("lot et designation par lot.xlsx")
    st.rerun()

# Barre latérale pour ajouter de nouvelles désignations
with st.sidebar:
    st.markdown("<h2>➕ Nouvelle Désignation</h2>", unsafe_allow_html=True)
    with st.form("form_add"):
        existing_lot_choice = st.selectbox("Lot existant", options=["Nouveau lot"] + sorted(st.session_state.lots_db["lots"].dropna().unique().tolist()))
        new_lot = st.text_input("Nom du lot", value="" if existing_lot_choice == "Nouveau lot" else existing_lot_choice, placeholder="Ex: Maçonnerie")
        new_designation = st.text_input("Désignation", placeholder="Ex: Mur porteur")
        add_btn = st.form_submit_button("Ajouter")
        if add_btn:
            ok, message = save_lot_designation(new_lot, new_designation)
            if ok:
                st.success(f"✅ {message}")
            else:
                st.error(message)

# Sélection des lots
st.markdown("<div class='card'><h2>📦 Sélection des Lots</h2>", unsafe_allow_html=True)
if not project_id:
    st.warning("Veuillez sélectionner ou créer un projet avant de choisir des lots.")
else:
    is_tracking = project_status == "suivi"
    # Charger les données existantes du projet
    c.execute('''
        SELECT lot, designation, unite, quantite, prix_unitaire, cout_total, duree, debut, fin,
               jours_ecoules, retard, avancement, paiement, image
        FROM project_details WHERE project_id = ?
    ''', (project_id,))
    project_data = c.fetchall()
    project_df = pd.DataFrame(project_data, columns=[
        "Lot", "Désignation", "Unité", "Quantité", "Prix Unitaire", "Coût Total", "Durée",
        "Début", "Fin", "Jours Écoulés", "Retard (j)", "Avancement (%)", "Paiement Engagé", "Image"
    ])
    default_values = {(row["Lot"], row["Désignation"]): row for _, row in project_df.iterrows()}
    scanned_key = str(project_id)

    with st.expander("📥 Importer un devis écrit / scanné", expanded=False):
        st.caption("Importez un PDF texte, un PDF scanné ou une image. Les lignes détectées sont proposées dans une table modifiable avant intégration au devis.")
        quote_file = st.file_uploader("Devis scanné ou PDF", type=["pdf", "png", "jpg", "jpeg"], key=f"quote_import_{project_id}")
        if quote_file and st.button("Lire et proposer les lignes du devis", key=f"parse_quote_{project_id}"):
            extracted_text, extraction_message = extract_text_from_uploaded_quote(quote_file)
            if extracted_text:
                parsed_df = parse_quote_text_to_rows(extracted_text, st.session_state.lots_db)
                if parsed_df.empty:
                    st.warning("Texte lu, mais aucune ligne exploitable n'a été détectée. Vous pouvez compléter la table manuellement.")
                    parsed_df = pd.DataFrame(columns=["Lot", "Désignation", "Unité", "Quantité", "Prix Unitaire", "Coût Total"])
                st.session_state.scanned_quote_rows[scanned_key] = parsed_df
                st.success(extraction_message)
                with st.expander("Voir le texte extrait"):
                    st.text_area("Texte détecté", extracted_text, height=180)
            else:
                st.warning(extraction_message)
        quote_rows = st.session_state.scanned_quote_rows.get(scanned_key)
        if quote_rows is not None:
            edited_quote_rows = st.data_editor(
                quote_rows,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Lot": st.column_config.TextColumn("Lot"),
                    "Désignation": st.column_config.TextColumn("Désignation"),
                    "Unité": st.column_config.SelectboxColumn("Unité", options=["m²", "ML", "U", "Forfait"]),
                    "Quantité": st.column_config.NumberColumn("Quantité", min_value=0.0, step=1.0),
                    "Prix Unitaire": st.column_config.NumberColumn("Prix Unitaire", min_value=0.0, step=1.0),
                    "Coût Total": st.column_config.NumberColumn("Coût Total", min_value=0.0, step=1.0),
                },
                key=f"quote_rows_editor_{project_id}"
            )
            edited_quote_rows["Coût Total"] = edited_quote_rows["Quantité"].fillna(0) * edited_quote_rows["Prix Unitaire"].fillna(0)
            st.session_state.scanned_quote_rows[scanned_key] = edited_quote_rows
            st.info("Ces lignes seront ajoutées au devis au moment de l'enregistrement.")
            if st.button("Vider les lignes importées", key=f"clear_quote_rows_{project_id}"):
                st.session_state.scanned_quote_rows.pop(scanned_key, None)
                st.rerun()

    lots_uniques = sorted(st.session_state.lots_db["lots"].unique())
    existing_lots = [lot for lot in sorted(project_df["Lot"].dropna().unique()) if lot in lots_uniques]
    selected_lots = st.multiselect("Choisir les lots", options=lots_uniques, default=existing_lots, placeholder="Sélectionnez un ou plusieurs lots")

    all_data = []
    if selected_lots:
        for lot in selected_lots:
            designations = st.session_state.lots_db[st.session_state.lots_db["lots"] == lot]["DESIGNATIONS"].unique().tolist()
            if normalize_label(lot) == "divers":
                designations = sorted(st.session_state.lots_db["DESIGNATIONS"].dropna().astype(str).unique().tolist())
            with st.expander(f"🔧 {lot}", expanded=True):
                designation_search = st.text_input("Commencer à saisir une désignation", key=f"search_{lot}", placeholder="Ex: peinture, terrasse, plomberie...")
                if designation_search:
                    search_norm = normalize_label(designation_search)
                    designations = [d for d in designations if normalize_label(d).startswith(search_norm)]
                    if not designations:
                        st.info("Aucune désignation ne commence par cette saisie.")
                existing_designations = project_df[project_df["Lot"] == lot]["Désignation"].dropna().tolist()
                selected_designations = st.multiselect(f"Désignations pour « {lot} »", options=designations, default=[d for d in existing_designations if d in designations], key=f"multi_{lot}")
                for d in selected_designations:
                    with st.container():
                        st.markdown(f"<h3>{d}</h3>", unsafe_allow_html=True)
                        default = default_values.get((lot, d), {})
                        default_unite = str(default.get("Unité", "m²") or "m²").strip()
                        if default_unite.lower() in ["ml", "m.l", "metre lineaire", "mètre linéaire"]:
                            default_unite = "ML"
                        else:
                            default_unite = "m²"
                        unite = st.selectbox("Unité", options=["m²", "ML"], index=0 if default_unite == "m²" else 1, key=f"u_{lot}_{d}")
                        quantite = st.number_input(f"Quantité", min_value=0.0, step=1.0, value=float(default.get("Quantité", 0.0)), key=f"q_{lot}_{d}")
                        prix_unitaire = st.number_input(f"Prix Unitaire", min_value=0.0, step=1.0, value=float(default.get("Prix Unitaire", 0.0)), key=f"p_{lot}_{d}")
                        cout_total = quantite * prix_unitaire
                        image_data = None
                        if is_tracking:
                            c4, c5 = st.columns(2)
                            duree = c4.number_input(f"Durée estimée (jours)", min_value=1, step=1, value=int(default.get("Durée", 1) or 1), key=f"duree_{lot}_{d}")
                            debut_default = datetime.strptime(default.get("Début", datetime.today().date().isoformat()), '%Y-%m-%d') if default.get("Début") else datetime.today().date()
                            debut = c5.date_input(f"Date début", value=debut_default, key=f"debut_{lot}_{d}")
                            fin = debut + timedelta(days=duree)
                            st.markdown(f"🗓️ Fin prévue : **{fin.strftime('%Y-%m-%d')}**")
                            jours_ecoules = (datetime.today().date() - debut).days
                            retard = max(0, jours_ecoules - duree)
                            paiement_default = float(default.get("Paiement Engagé", 0.0) or 0.0)
                            paiement_max = float(cout_total or 0.0)
                            if paiement_max > 0:
                                paiement_default = min(paiement_default, paiement_max)
                            paiement = st.number_input(
                                "Paiement engagé pour démarrer les travaux",
                                min_value=0.0,
                                max_value=paiement_max if paiement_max > 0 else None,
                                step=100.0,
                                value=paiement_default,
                                key=f"paiement_{lot}_{d}",
                                help="Le pourcentage d'avancement est calculé automatiquement selon le paiement engagé par rapport au coût total du lot."
                            )
                            avancement = int(round((paiement / cout_total) * 100)) if cout_total else 0
                            avancement = max(0, min(100, avancement))
                            st.markdown(f"**Avancement automatique : {avancement}%** du coût du lot")
                            deadline_info = deadline_status(duree, debut, avancement)
                            if deadline_alerts_enabled:
                                render_deadline_bar(f"{lot} - {d}", deadline_info)
                            image_key = f"img_{lot}_{d}"
                            uploaded_image = st.file_uploader("📸 Joindre une photo de visite chantier", type=["jpg", "png"], key=image_key)
                            image_data = default.get("Image", None)
                            if uploaded_image:
                                image_data = uploaded_image.read()
                                st.session_state.uploaded_images[image_key] = base64.b64encode(image_data).decode('utf-8')
                                st.image(uploaded_image, width=200)
                            elif image_data:
                                st.image(base64.b64decode(image_data), width=200, caption="Photo enregistrée")
                            image_data = st.session_state.uploaded_images.get(image_key, image_data)
                        else:
                            duree = int(default.get("Durée", 1) or 1)
                            debut = datetime.today().date()
                            fin = debut + timedelta(days=duree)
                            jours_ecoules = 0
                            retard = 0
                            avancement = 0
                            paiement = 0.0
                            deadline_info = deadline_status(duree, debut, avancement)
                        all_data.append({
                            "Lot": lot,
                            "Désignation": d,
                            "Unité": unite,
                            "Quantité": quantite,
                            "Prix Unitaire": prix_unitaire,
                            "Coût Total": cout_total,
                            "Durée": duree,
                            "Début": debut,
                            "Fin": fin,
                            "Jours Écoulés": jours_ecoules,
                            "Retard (j)": retard,
                            "Avancement (%)": avancement,
                            "Paiement Engagé": paiement,
                            "Image": image_data,
                            "Progression délai (%)": deadline_info["time_percent"],
                            "Jours restants": deadline_info["remaining_days"],
                            "Alerte délai": deadline_info["alert_text"] if deadline_alerts_enabled else "",
                            "Updated At": datetime.now().isoformat()
                        })

    imported_rows = st.session_state.scanned_quote_rows.get(scanned_key)
    if imported_rows is not None and not imported_rows.empty:
        for _, imported in imported_rows.iterrows():
            lot = str(imported.get("Lot") or "Divers").strip() or "Divers"
            designation = str(imported.get("Désignation") or "").strip()
            if not designation:
                continue
            unite = str(imported.get("Unité") or "m²").strip()
            quantite = float(imported.get("Quantité") or 0)
            prix_unitaire = float(imported.get("Prix Unitaire") or 0)
            cout_total = quantite * prix_unitaire
            default = default_values.get((lot, designation), {})
            duree = int(default.get("Durée", 1) or 1)
            debut = datetime.today().date()
            fin = debut + timedelta(days=duree)
            paiement = float(default.get("Paiement Engagé", 0.0) or 0.0) if is_tracking else 0.0
            avancement = int(round((paiement / cout_total) * 100)) if cout_total else 0
            deadline_info = deadline_status(duree, debut, avancement)
            all_data.append({
                "Lot": lot,
                "Désignation": designation,
                "Unité": unite,
                "Quantité": quantite,
                "Prix Unitaire": prix_unitaire,
                "Coût Total": cout_total,
                "Durée": duree,
                "Début": debut,
                "Fin": fin,
                "Jours Écoulés": 0,
                "Retard (j)": 0,
                "Avancement (%)": avancement,
                "Paiement Engagé": paiement,
                "Image": default.get("Image", None),
                "Progression délai (%)": deadline_info["time_percent"],
                "Jours restants": deadline_info["remaining_days"],
                "Alerte délai": deadline_info["alert_text"] if deadline_alerts_enabled else "",
                "Updated At": datetime.now().isoformat()
            })

    if all_data:
            df = pd.DataFrame(all_data)
            panel_title = "📄 Devis initial" if not is_tracking else "📄 Devis global & suivi d'avancement"
            st.markdown(f"<div class='card'><h2>{panel_title}</h2>", unsafe_allow_html=True)
            display_columns = ["Lot", "Désignation", "Unité", "Quantité", "Prix Unitaire", "Coût Total"]
            total_paiement = df["Paiement Engagé"].sum()
            total_cout = df["Coût Total"].sum()
            taux_amort = (total_paiement / total_cout * 100) if total_cout else 0
            taux_moyen = df["Avancement (%)"].mean()

            # Calcul du besoin de financement
            current_advance = get_total_advances(c, project_id)
            besoin_financement = current_advance - total_paiement
            if is_tracking:
                render_tracking_report_html(
                    df,
                    total_cout,
                    total_paiement,
                    current_advance,
                    besoin_financement,
                    taux_moyen
                )
                if deadline_alerts_enabled:
                    st.markdown("<div class='card'><h2>Alertes délais</h2>", unsafe_allow_html=True)
                    render_deadline_alert_summary(df)
                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.dataframe(df[display_columns], use_container_width=True, hide_index=True)
                st.markdown(f"<div class='design-kpi'><small>Total devis TTC</small><strong>{total_cout:.2f} DT</strong></div>", unsafe_allow_html=True)

            # Enregistrer les détails du projet dans la base de données
            if st.button("💾 Enregistrer le devis" if not is_tracking else "💾 Enregistrer les modifications"):
                save_timestamp = datetime.now().isoformat()
                history_entries_added = 0
                for row in df.to_dict('records'):
                    if is_tracking and should_add_history_entry(c, project_id, row):
                        history_entries_added += 1
                        c.execute('''
                            INSERT INTO project_history (project_id, lot, designation, avancement, paiement, image, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            project_id,
                            row["Lot"],
                            row["Désignation"],
                            row["Avancement (%)"],
                            row["Paiement Engagé"],
                            row["Image"],
                            save_timestamp
                        ))
                    # Mettre à jour ou insérer la dernière version
                    c.execute('''
                        INSERT OR REPLACE INTO project_details (
                            project_id, lot, designation, unite, quantite, prix_unitaire, cout_total,
                            duree, debut, fin, jours_ecoules, retard, avancement, paiement, image, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        project_id,
                        row["Lot"],
                        row["Désignation"],
                        row["Unité"],
                        row["Quantité"],
                        row["Prix Unitaire"],
                        row["Coût Total"],
                        row["Durée"],
                        row["Début"].isoformat(),
                        row["Fin"].isoformat(),
                        row["Jours Écoulés"],
                        row["Retard (j)"],
                        row["Avancement (%)"],
                        row["Paiement Engagé"],
                        row["Image"],
                        save_timestamp
                    ))
                conn.commit()
                if is_tracking:
                    st.success(f"Modifications enregistrées. {history_entries_added} nouvelle(s) ligne(s) ajoutée(s) à l'historique.")
                else:
                    st.success("Devis enregistré avec succès !")

            if not is_tracking:
                if st.button("✅ Devis validé par le client - passer au suivi chantier"):
                    for row in df.to_dict('records'):
                        c.execute('''
                            INSERT OR REPLACE INTO project_details (
                                project_id, lot, designation, unite, quantite, prix_unitaire, cout_total,
                                duree, debut, fin, jours_ecoules, retard, avancement, paiement, image, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            project_id,
                            row["Lot"],
                            row["Désignation"],
                            row["Unité"],
                            row["Quantité"],
                            row["Prix Unitaire"],
                            row["Coût Total"],
                            row["Durée"],
                            row["Début"].isoformat(),
                            row["Fin"].isoformat(),
                            row["Jours Écoulés"],
                            row["Retard (j)"],
                            0,
                            0,
                            None,
                            row["Updated At"]
                        ))
                    c.execute("UPDATE projects SET project_status = ?, validated_at = ? WHERE project_id = ?",
                              ("suivi", datetime.now().isoformat(), project_id))
                    conn.commit()
                    st.success("Devis validé. Le projet passe en suivi de réalisation.")
                    st.rerun()

            def generate_pdf(df):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_fill_color(255, 255, 255)
                title = "Devis global" if not is_tracking else "Devis global et suivi d'avancement"
                add_pdf_header(pdf, title, selected_client, selected_project)
                temp_assets = []
                draw_project_pdf_table(pdf, df, include_tracking=is_tracking, temp_assets=temp_assets)
                pdf.ln(8)
                y = pdf.get_y()
                pdf.set_fill_color(*BRAND_NAVY)
                pdf.rect(10, y, 66, 24, "F")
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Arial", 'B', 8)
                pdf.text(15, y + 9, "TOTAL DEVIS TTC")
                pdf.set_text_color(*BRAND_TEAL)
                pdf.set_font("Arial", 'B', 17)
                pdf.text(15, y + 19, safe_text(f"{total_cout:.2f} DT"))
                if is_tracking:
                    pdf_kpi_card(pdf, 82, y, "Paiement engagé", f"{total_paiement:.2f} DT", BRAND_TEAL)
                    pdf_kpi_card(pdf, 144, y, "Avance perçue", f"{current_advance:.2f} DT", (242, 142, 43), width=56)
                    y2 = y + 26
                    if besoin_financement < 0:
                        pdf_kpi_card(pdf, 82, y2, "Besoin financement", f"{-besoin_financement:.2f} DT", (200, 72, 72))
                    else:
                        pdf_kpi_card(pdf, 82, y2, "Excédent financement", f"{besoin_financement:.2f} DT", (91, 68, 158))
                    pdf_kpi_card(pdf, 144, y2, "Taux moyen réalisation", f"{taux_moyen:.2f}%", (41, 137, 202), width=56)
                else:
                    pdf_kpi_card(pdf, 82, y, "Statut", "Devis initial", BRAND_TEAL, width=58)
                    pdf_kpi_card(pdf, 144, y, "Avance", "Non saisie", (242, 142, 43), width=56)
                pdf_footer(pdf)
                output = BytesIO()
                temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                temp_pdf.close()
                pdf.output(dest='F', name=temp_pdf.name)
                with open(temp_pdf.name, 'rb') as f:
                    output.write(f.read())
                output.seek(0)
                os.remove(temp_pdf.name)
                for asset_path in temp_assets:
                    if os.path.exists(asset_path):
                        os.remove(asset_path)
                return output

            def generate_history_pdf():
                pdf = FPDF()
                pdf.add_page()
                add_pdf_header(pdf, "Etat d'avancement chantier", selected_client, selected_project)
                temp_assets = []
                draw_project_pdf_table(pdf, df, include_tracking=True, temp_assets=temp_assets)
                pdf.ln(8)
                y = pdf.get_y()
                pdf.set_fill_color(*BRAND_NAVY)
                pdf.rect(10, y, 66, 24, "F")
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Arial", 'B', 8)
                pdf.text(15, y + 9, "TOTAL DEVIS TTC")
                pdf.set_text_color(*BRAND_TEAL)
                pdf.set_font("Arial", 'B', 17)
                pdf.text(15, y + 19, safe_text(f"{total_cout:.2f} DT"))
                pdf_kpi_card(pdf, 82, y, "Paiement engagé", f"{total_paiement:.2f} DT", BRAND_TEAL)
                pdf_kpi_card(pdf, 144, y, "Avance perçue", f"{current_advance:.2f} DT", (242, 142, 43), width=56)
                y2 = y + 26
                if besoin_financement < 0:
                    pdf_kpi_card(pdf, 82, y2, "Besoin financement", f"{-besoin_financement:.2f} DT", (200, 72, 72))
                else:
                    pdf_kpi_card(pdf, 82, y2, "Excédent financement", f"{besoin_financement:.2f} DT", (91, 68, 158))
                pdf_kpi_card(pdf, 144, y2, "Taux moyen réalisation", f"{taux_moyen:.2f}%", (41, 137, 202), width=56)
                pdf_footer(pdf)

                output = BytesIO()
                temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                temp_pdf.close()
                pdf.output(dest='F', name=temp_pdf.name)
                with open(temp_pdf.name, 'rb') as f:
                    output.write(f.read())
                output.seek(0)
                os.remove(temp_pdf.name)
                for asset_path in temp_assets:
                    if os.path.exists(asset_path):
                        os.remove(asset_path)
                return output

            pdf_bytes = generate_pdf(df)
            st.download_button("📅 Télécharger le devis PDF", data=pdf_bytes, file_name=f"devis_{selected_client}_{selected_project}.pdf", mime="application/pdf")
            if is_tracking:
                history_pdf_bytes = generate_history_pdf()
                st.download_button("📊 Télécharger l'état d'avancement PDF", data=history_pdf_bytes, file_name=f"etat_avancement_{selected_client}_{selected_project}.pdf", mime="application/pdf")

conn.close()
