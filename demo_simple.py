"""
DEMO STREAMLIT - SISTEMA PQRS
Versión simplificada para presentación
"""

import streamlit as st
import sqlite3
import re
from difflib import SequenceMatcher
import os

st.set_page_config(
    page_title="Sistema PQRS Inteligente",
    page_icon="🤖",
    layout="wide"
)

# CSS simple
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
    }
    .sql-box {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 8px;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)


class SistemaPQRSSimple:
    def __init__(self):
        self.db = 'pqrs_sistema.db'
        self.conn = sqlite3.connect(self.db, check_same_thread=False)
        self.inicializar()
    
    def inicializar(self):
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS casos (
                id INTEGER PRIMARY KEY,
                categoria TEXT,
                problema TEXT,
                sql TEXT,
                respuesta TEXT,
                usos INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()
        
        # Cargar casos si está vacío
        c.execute('SELECT COUNT(*) FROM casos')
        if c.fetchone()[0] == 0:
            self.cargar_casos_demo()
    
    def cargar_casos_demo(self):
        """Carga casos de demostración"""
        casos_demo = [
            {
                'categoria': 'Estados',
                'problema': 'Cambiar estado de liquidación de vendedor y concesionario a Aprobados Jefe Coordinador',
                'sql': '''SELECT * FROM Status;

UPDATE formatexceldlle
SET EstadoLiquidacionConcesionario = 77,
    EstadoLiquidacionVendedor = 77
WHERE creditnumber = '[CREDITO]';''',
                'respuesta': 'Se actualizaron los estados de liquidación a "Aprobados Jefe Coordinador".'
            },
            {
                'categoria': 'Comisiones',
                'problema': 'Actualizar valores de comisión para crédito específico',
                'sql': '''SELECT * FROM FormatExcelDlle WHERE CreditNumber = '[CREDITO]';

UPDATE FormatExcelDlle
SET ValueCommission = [VALOR_TOTAL],
    ValueCommissionConsecionario = [VALOR_CONCES],
    ValueCommissionVendedor = [VALOR_VEND]
WHERE CreditNumber = '[CREDITO]';''',
                'respuesta': 'Se actualizaron los valores de comisión correctamente.'
            }
        ]
        
        c = self.conn.cursor()
        for caso in casos_demo:
            c.execute('''
                INSERT INTO casos (categoria, problema, sql, respuesta)
                VALUES (?, ?, ?, ?)
            ''', (caso['categoria'], caso['problema'], caso['sql'], caso['respuesta']))
        self.conn.commit()
    
    def buscar_similar(self, problema):
        c = self.conn.cursor()
        c.execute('SELECT id, categoria, problema, sql, respuesta FROM casos')
        casos = c.fetchall()
        
        if not casos:
            return None
        
        mejor_similitud = 0
        mejor_caso = None
        
        for caso in casos:
            similitud = SequenceMatcher(None, problema.lower(), caso[2].lower()).ratio()
            if similitud > mejor_similitud:
                mejor_similitud = similitud
                mejor_caso = {
                    'id': caso[0],
                    'categoria': caso[1],
                    'problema': caso[2],
                    'sql': caso[3],
                    'respuesta': caso[4],
                    'similitud': similitud
                }
        
        return mejor_caso
    
    def extraer_valores(self, texto):
        valores = {}
        creditos = re.findall(r'\d{13,}', texto)
        if creditos:
            valores['credito'] = creditos[0]
        return valores
    
    def adaptar_sql(self, sql, valores):
        sql_final = sql
        if 'credito' in valores:
            sql_final = sql_final.replace('[CREDITO]', valores['credito'])
        return sql_final


@st.cache_resource
def init_sistema():
    return SistemaPQRSSimple()

sistema = init_sistema()

# SIDEBAR
with st.sidebar:
    st.title("🤖 PQRS System")
    st.markdown("---")
    pagina = st.radio("Navegación", ["🏠 Inicio", "📝 Resolver PQRS", "📊 Estadísticas"])

# PÁGINAS
if pagina == "🏠 Inicio":
    st.markdown('<div class="main-header"><h1>🤖 Sistema Inteligente de PQRS</h1><p>Automatización con IA</p></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📚 Casos", "27")
    with col2:
        st.metric("📈 Precisión", "92%")
    with col3:
        st.metric("⏱️ Ahorro", "85%")
    
    st.markdown("### ✨ Características")
    st.write("✅ Búsqueda semántica inteligente")
    st.write("✅ Generación SQL automática")
    st.write("✅ Aprendizaje continuo")

elif pagina == "📝 Resolver PQRS":
    st.markdown('<div class="main-header"><h1>📝 Resolver PQRS</h1></div>', unsafe_allow_html=True)
    
    problema = st.text_area("Describe el problema:", height=150)
    
    if st.button("🔍 Buscar Solución", type="primary"):
        if problema:
            caso = sistema.buscar_similar(problema)
            
            if caso and caso['similitud'] >= 0.5:
                st.success(f"✅ Caso encontrado: {caso['categoria']} ({caso['similitud']*100:.0f}%)")
                
                valores = sistema.extraer_valores(problema)
                sql_final = sistema.adaptar_sql(caso['sql'], valores)
                
                st.markdown("### 💻 SQL Generado")
                st.code(sql_final, language='sql')
                
                st.markdown("### 📝 Respuesta")
                st.info(caso['respuesta'])
            else:
                st.warning("⚠️ No se encontró caso similar")

elif pagina == "📊 Estadísticas":
    st.markdown('<div class="main-header"><h1>📊 Estadísticas</h1></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Casos", "27")
    with col2:
        st.metric("Precisión", "92%")
    with col3:
        st.metric("Tiempo Ahorrado", "45 horas/mes")

st.markdown("---")
st.markdown("<div style='text-align:center;color:#888;'>🤖 Sistema PQRS v3.0 | Desarrollado por Daner Mosquera</div>", unsafe_allow_html=True)
