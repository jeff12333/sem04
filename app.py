from flask import Flask, render_template, request, send_file
import os
import pandas as pd
import time
import random
import subprocess
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_chrome_version():
    try:
        output = subprocess.check_output(['chromium', '--version']).decode('utf-8')
        version = re.search(r'Chromium (\d+)', output).group(1)
        return int(version)
    except Exception as e:
        print(f"No se pudo detectar versión: {e}")
        return None

def configurar_driver():
    options = uc.ChromeOptions()
    os.environ["DISPLAY"] = ":99"
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    options.add_argument(f'--user-agent={ua}')
    
    driver = uc.Chrome(
        options=options, 
        version_main=get_chrome_version(),
        headless=False,
        use_subprocess=True
    ) 
    return driver

def procesar_onpe(file_path):
    try:
        df_input = pd.read_excel(file_path)
        df_input.columns = [c.lower().strip() for c in df_input.columns]
        dnis = df_input['dni'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().tolist()
    except Exception as e:
        print(f"Error leyendo Excel: {e}")
        return None

    print(f"\n--- INICIANDO PROCESO: Se detectaron {len(dnis)} DNIs en el archivo ---")
    
    driver = configurar_driver()
    if not driver: return None
        
    resultados = []

    try:
        for idx, dni in enumerate(dnis):
            if len(dni) < 8: continue
            
            print(f"[{idx+1}/{len(dnis)}] Consultando DNI {dni}...")
            res_dni = {"DNI": dni, "Estado": "Fallo técnico", "Ubicacion": "N/A", "Local": "N/A"}

            try:
                # 1. Recargar la página limpia por cada DNI (más seguro que usar driver.back)
                driver.get("https://consultaelectoral.onpe.gob.pe/inicio")
                time.sleep(random.uniform(3, 5))

                wait = WebDriverWait(driver, 20)
                
                # 2. Escribir DNI
                input_dni = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='tel']")))
                input_dni.clear()
                for char in dni:
                    input_dni.send_keys(char)
                    time.sleep(random.uniform(0.1, 0.2))
                
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", input_dni)
                time.sleep(1)

                # 3. Clic
                btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button_consulta")))
                ActionChains(driver).move_to_element(btn).pause(random.uniform(0.5, 1.0)).click().perform()

                # 4. Esperar que cargue la tabla o salga un error real
                wait.until(lambda d: d.find_elements(By.CLASS_NAME, "m_mesa") or "ERROR 500" in d.page_source.upper() or "INTERNAL SERVER ERROR" in d.page_source.upper())
                
                time.sleep(3)
                source = driver.page_source.upper()

                # 5. Verificación corregida (ya no busca el número "500" suelto)
                if "ERROR 500" in source or "INTERNAL SERVER ERROR" in source:
                    print(f"¡BLOQUEO DETECTADO! Servidor de ONPE rechazó la conexión.")
                    res_dni["Estado"] = "Bloqueo IP"
                    resultados.append(res_dni)
                    break # Aquí sí nos detenemos porque la ONPE nos bloqueó

                elif "MIEMBRO DE MESA" in source:
                    try:
                        m_text = driver.find_element(By.CLASS_NAME, "m_mesa").text.upper()
                        res_dni["Estado"] = "NO" if "NO ERES" in m_text else "SI"
                        res_dni["Ubicacion"] = driver.find_element(By.CLASS_NAME, "local").text.strip()
                        res_dni["Local"] = driver.find_element(By.CLASS_NAME, "dato").text.strip()
                        print(f"    -> Éxito: Datos extraídos.")
                    except:
                        res_dni["Estado"] = "Error leyendo datos de la web"
                else:
                    res_dni["Estado"] = "DNI no encontrado"

            except Exception as e:
                print(f"    -> Error técnico en DNI {dni}: {str(e)[:40]}")
            
            resultados.append(res_dni)

            # 6. Pausa humana (Solo si no es el último DNI)
            if idx < len(dnis) - 1:
                pausa = random.uniform(15, 25)
                print(f"    -> Esperando {int(pausa)}s para no saturar el servidor...")
                time.sleep(pausa)

    finally:
        try:
            driver.quit()
        except:
            pass
        
        print(f"\nGenerando archivo Excel con {len(resultados)} registros procesados...")
        output_filename = f"resultado_onpe_{int(time.time())}.xlsx"
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        pd.DataFrame(resultados).to_excel(output_path, index=False)
        
    return output_path

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith(('.xlsx', '.xls')):
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)
            res_path = procesar_onpe(path)
            if res_path and os.path.exists(res_path):
                return send_file(res_path, as_attachment=True)
            else:
                return "Error crítico al generar el archivo. Verifica los logs.", 500
                
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)