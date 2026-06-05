import streamlit as st
import pandas as pd
import os
import unicodedata

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Mi Polla Mundial", layout="wide")

# --- FUNCIONES DE DATOS ---
def cargar_csv(archivo, columnas):
    if not os.path.exists(archivo): return pd.DataFrame(columns=columnas)
    return pd.read_csv(archivo)

def registrar_usuario(username, nombre, celular, email):
    # Ajustado a las columnas reales de tu CSV
    df = cargar_csv('usuarios.csv', ['username', 'name', 'phone', 'email'])
    if username in df['username'].values: return False, "Usuario existente"
    nuevo = pd.DataFrame([{'username': username, 'name': nombre, 'phone': celular, 'email': email}])
    df = pd.concat([df, nuevo], ignore_index=True)
    df.to_csv('usuarios.csv', index=False)
    return True, "Registro exitoso"

def validar_login(username):
    # Login basado solo en usuario (no hay contraseñas en el CSV)
    df = cargar_csv('usuarios.csv', ['username', 'name', 'phone', 'email'])
    user = df[df['username'] == username]
    return not user.empty

def guardar_prediccion(username, index, gl, gv, res):
    df = cargar_csv('predicciones.csv', ['username', 'index', 'gl', 'gv', 'res'])
    nueva = pd.DataFrame([{'username': username, 'index': index, 'gl': gl, 'gv': gv, 'res': res}])
    df = df[~((df['username'] == username) & (df['index'] == index))]
    df = pd.concat([df, nueva], ignore_index=True)
    df.to_csv('predicciones.csv', index=False)

# --- LÓGICA DE BANDERAS ---
def get_flag_url(pais):
    codes = {
        "mexico":"mx", "sudafrica":"za", "japon":"jp", "brasil":"br", "francia":"fr", 
        "argentina":"ar", "espana":"es", "inglaterra":"gb-eng", "portugal":"pt", 
        "alemania":"de", "italia":"it", "chile":"cl", "croacia":"hr", "canada":"ca", 
        "australia":"au", "eeuu":"us", "suiza":"ch", "marruecos":"ma", 
        "colombia":"co", "iran":"ir", "ecuador":"ec", "costa rica":"cr", 
        "polonia":"pl", "belgica":"be", "senegal":"sn", "paises bajos":"nl", 
        "arabia saudita":"sa", "uruguay":"uy", "nigeria":"ng", "corea del sur":"kr",
        "estados unidos":"us", "ee.uu.":"us"
    }
    nombre = unicodedata.normalize('NFKD', str(pais)).encode('ASCII', 'ignore').decode('utf-8').lower().strip()
    return f"https://flagcdn.com/w80/{codes[nombre]}.png" if nombre in codes else None

def actualizar_resultado(index, local, visitante):
    gl = st.session_state.get(f"gl_{index}", 0)
    gv = st.session_state.get(f"gv_{index}", 0)
    if gl > gv: st.session_state[f"res_{index}"] = f"Gana {local}"
    elif gv > gl: st.session_state[f"res_{index}"] = f"Gana {visitante}"
    else: st.session_state[f"res_{index}"] = "Empate"

# --- INTERFAZ PRINCIPAL ---
st.title("⚽ Mis Predicciones")

# --- CONTADOR DE USUARIOS ---
df_users = cargar_csv('usuarios.csv', ['username', 'name', 'phone', 'email'])
st.metric(label="Total de participantes registrados", value=len(df_users))

# --- SIDEBAR: LOGIN / REGISTRO ---
if 'current_user' not in st.session_state: st.session_state.current_user = None

with st.sidebar:
    st.header("🔐 Acceso")
    if not st.session_state.current_user:
        modo = st.radio("Acción", ["Iniciar Sesión", "Registrarse"])
        
        if modo == "Registrarse":
            # Formulario con limpieza automática
            with st.form("registro_form", clear_on_submit=True):
                u_in = st.text_input("Usuario*")
                n_in = st.text_input("Nombre completo*")
                c_in = st.text_input("Teléfono")
                e_in = st.text_input("Correo")
                
                if st.form_submit_button("Registrar"):
                    if u_in and n_in:
                        ok, msg = registrar_usuario(u_in, n_in, c_in, e_in)
                        if ok: 
                            st.success(msg)
                            st.rerun()
                        else: st.error(msg)
                    else: st.error("Completa usuario y nombre")
        
        else: # Iniciar Sesión
            u_in = st.text_input("Usuario")
            if st.button("Entrar"):
                if validar_login(u_in):
                    st.session_state.current_user = u_in
                    st.rerun()
                else: st.error("Usuario no encontrado")
    else:
        st.success(f"Hola, {st.session_state.current_user}")
        if st.button("Cerrar Sesión"):
            st.session_state.current_user = None
            st.rerun()

# --- TABLA DE PARTIDOS ---
tab1, tab2, tab3 = st.tabs(["⚽ Predicciones", "🏆 Ranking", "🔐 Admin"])

with tab1:
    if os.path.exists('partidos.csv'):
        df = pd.read_csv('partidos.csv')
        
        if st.button("💾 GUARDAR TODAS MIS PREDICCIONES", type="primary", use_container_width=True):
            if st.session_state.current_user:
                for i in range(len(df)):
                    guardar_prediccion(st.session_state.current_user, i, st.session_state.get(f"gl_{i}", 0), st.session_state.get(f"gv_{i}", 0), st.session_state.get(f"res_{i}", "Empate"))
                st.success("Guardado correctamente")
            else:
                st.warning("⚠️ Debes iniciar sesión para guardar.")

        for i, row in df.iterrows():
            if f"res_{i}" not in st.session_state: st.session_state[f"res_{i}"] = "Empate"
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 2, 3, 1])
                with c1:
                    st.write(f"**{row['Local']}** vs **{row['Visitante']}**")
                    f1, f2 = st.columns(2)
                    flag_l = get_flag_url(row['Local'])
                    flag_v = get_flag_url(row['Visitante'])
                    if flag_l: f1.image(flag_l, width=40)
                    if flag_v: f2.image(flag_v, width=40)
                with c2:
                    st.number_input("GL", 0, 99, key=f"gl_{i}", on_change=actualizar_resultado, args=(i, row['Local'], row['Visitante']))
                    st.number_input("GV", 0, 99, key=f"gv_{i}", on_change=actualizar_resultado, args=(i, row['Local'], row['Visitante']))
                with c3:
                    st.radio("Res", ["Empate", f"Gana {row['Local']}", f"Gana {row['Visitante']}"], key=f"res_{i}", label_visibility="collapsed")
                with c4:
                    if st.button("💾", key=f"btn_{i}"):
                        if st.session_state.current_user:
                            guardar_prediccion(st.session_state.current_user, i, st.session_state[f"gl_{i}"], st.session_state[f"gv_{i}"], st.session_state[f"res_{i}"])
                            st.toast("Guardado")
                        else:
                            st.warning("Inicia sesión")

with tab2:
    st.title("🏆 Ranking")
    st.info("Próximamente disponible.")

with tab3:
    st.title("🔐 Administración")
    pwd = st.text_input("Contraseña", type="password")
    if pwd == "admin1234":
        st.subheader("Subir Resultados")
        st.file_uploader("Cargar CSV", type="csv")
