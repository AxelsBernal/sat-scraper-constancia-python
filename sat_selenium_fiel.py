import os
import time
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime
import json

# --- Importaciones de Selenium ---
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    NoSuchFrameException,
    WebDriverException,
    # FileNotFoundError no existe en Selenium, se usa la de Python
)


# =======================================================
# 1. CONFIGURACIÓN
# =======================================================

# Usar segundos en lugar de Duration de Java
TIMEOUT_DURATION_SECONDS = 60
WAIT_FOR_ELEMENT_SECONDS = 12
# Path usa Pathlib.cwd() (similar a System.getProperty("user.dir"))
SCREENSHOT_DIR = Path.cwd() / "screenshots"
DEFAULT_FINAL_PDF_NAME = "constancia_sat.pdf"

# 🚀 Rutas y Contraseña Personalizadas (¡REEMPLAZA ESTAS RUTAS!)
# Usar Path() con raw strings (r"...") o Path().resolve()
DEFAULT_CER_PATH = Path(r"C:\Users\****")
DEFAULT_KEY_PATH = Path(r"C:\Users\****")
DEFAULT_KEY_PASS = "****"


# =======================================================
# 2. UTILIDADES BÁSICAS DE SELENIUM Y ARCHIVOS
# =======================================================

def sleep(seconds: float):
    """Pausa la ejecución (similar a Thread.sleep de Java)."""
    time.sleep(seconds)

def take_screenshot(driver: webdriver.Chrome, label: str):
    """Guarda un screenshot con timestamp (función desactivada para el headless por defecto)."""
    try:
        # Esta función puede no ser útil en modo headless, pero se mantiene la lógica
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        safe_label = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in label)
        filename = f"{timestamp}_{safe_label}.png"
        full_path = SCREENSHOT_DIR / filename
        
        driver.get_screenshot_as_file(str(full_path))
        print(f"[SS] Capturado: {full_path}")
    except Exception as e:
        print(f"[SS] No se pudo guardar screenshot '{label}': {e}")


def scroll_horizontal_all_the_way(driver: webdriver.Chrome):
    """Desplaza a la derecha todos los contenedores con scroll horizontal (JS)."""
    js = """
        try {
            const root = document.scrollingElement || document.documentElement || document.body;
            if (root && root.scrollWidth - root.clientWidth > 5) {
                root.scrollLeft = root.scrollWidth;
            }
            const nodes = Array.from(document.querySelectorAll('*'));
            for (const el of nodes) {
                const sw = el.scrollWidth || 0;
                const cw = el.clientWidth || 0;
                if (sw - cw > 5) {
                    el.scrollLeft = sw;
                }
            }
        } catch (e) {
            console.log('scroll_horizontal_all_the_way error', e);
        }
        """
    driver.execute_script(js)

def find_first_present(driver: webdriver.Chrome, *locators) -> Optional[webdriver.remote.webelement.WebElement]:
    """Busca el primer elemento presente en el DOM, esperando hasta 12 segundos."""
    wait = WebDriverWait(driver, WAIT_FOR_ELEMENT_SECONDS)
    for locator in locators:
        try:
            return wait.until(EC.presence_of_element_located(locator))
        except TimeoutException:
            pass
    return None

def find_first_clickable(driver: webdriver.Chrome, *locators) -> Optional[webdriver.remote.webelement.WebElement]:
    """Busca el primer elemento que sea clicable, esperando hasta 12 segundos."""
    wait = WebDriverWait(driver, WAIT_FOR_ELEMENT_SECONDS)
    for locator in locators:
        try:
            return wait.until(EC.element_to_be_clickable(locator))
        except TimeoutException:
            pass
    return None

def click_by_inner_text_js(driver: webdriver.Chrome, needles: List[str]) -> bool:
    """Intenta hacer clic en un elemento usando su texto visible (JS)."""
    script = """
        const needles = Array.from(arguments[0] || []).map(s => (s||'').trim().toLowerCase());
        function isVisible(el){
          if (!el) return false;
          const r = el.getBoundingClientRect();
          const style = window.getComputedStyle(el);
          return r.width > 1 && r.height > 1 &&
                 style.visibility !== 'hidden' &&
                 style.display !== 'none' &&
                 style.opacity !== '0';
        }
        const candidates = Array.from(document.querySelectorAll('button,a,[role="button"],input[type="button"],input[type="submit"],div,span,label'));
        for (const el of candidates){
          const txt = (el.innerText || el.textContent || '').trim().toLowerCase();
          if (!txt) continue;
          if (!isVisible(el)) continue;
          if (needles.some(n => n && txt.includes(n))){
            try {
              el.scrollIntoView({behavior:'instant', block:'center', inline:'center'});
              el.click();
              return true;
            } catch (e) {}
          }
        }
        return false;
        """
    result = driver.execute_script(script, needles)
    return bool(result)

def switch_to_login_frame_if_any(driver: webdriver.Chrome):
    """Busca y cambia al iframe que contenga campos de login/e.firma."""
    driver.switch_to.default_content()
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for frame in iframes:
        try:
            driver.switch_to.frame(frame)
            inputs = driver.find_elements(By.XPATH,
                    "//input[@type='text' or @type='email' or @type='password' or @type='file']")
            if inputs:
                return 
            driver.switch_to.default_content()
        except NoSuchFrameException:
            driver.switch_to.default_content()
        except Exception:
            driver.switch_to.default_content()
    driver.switch_to.default_content()

def try_click_in_current_context(driver: webdriver.Chrome, locators: List[tuple], timeout_seconds: float) -> bool:
    """Intenta localizar y hacer click en el botón dentro del contexto (frame) actual."""
    wait = WebDriverWait(driver, timeout_seconds)
    for locator in locators:
        try:
            btn = wait.until(EC.element_to_be_clickable(locator))

            driver.execute_script(
                    "arguments[0].scrollIntoView({behavior:'instant', block:'center', inline:'center'});",
                    btn
            )
            sleep(0.8)

            try:
                btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", btn)
            
            return True
        except TimeoutException:
            pass
    return False

def click_generar_constancia_btn(driver: webdriver.Chrome):
    """Busca el botón 'Generar Constancia' y hace click."""
    
    locators = [
        (By.ID, "formReimpAcuse:j_idt50"),
        (By.XPATH, "//button[.//span[contains(normalize-space(.),'Generar Constancia')]]"),
        (By.XPATH, "//span[contains(normalize-space(.),'Generar Constancia')]/ancestor::button[1]"),
        (By.XPATH, "//button[contains(normalize-space(.),'Generar Constancia')]"),
    ]

    # 1) Intentar en el DOM principal
    driver.switch_to.default_content()
    if try_click_in_current_context(driver, locators, WAIT_FOR_ELEMENT_SECONDS):
        return

    # 2) Si no se encontró, recorrer todos los iframes
    frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
    for idx, frame in enumerate(frames):
        try:
            driver.switch_to.default_content()
            WebDriverWait(driver, 5).until(
                    EC.frame_to_be_available_and_switch_to_it(frame)
            )
        except Exception:
            continue

        if try_click_in_current_context(driver, locators, WAIT_FOR_ELEMENT_SECONDS):
            driver.switch_to.default_content()
            return
        
        driver.switch_to.default_content()

    # 3) Fallo
    raise NoSuchElementException(
            "No se encontró el botón para generar/descargar la Constancia. El portal SAT pudo haber cambiado su estructura (DOM)."
    )


# =======================================================
# 3. LÓGICA DE E.FIRMA
# =======================================================

def select_efirma_tab(driver: webdriver.Chrome):
    """Selecciona la pestaña/botón de 'e.firma' de forma robusta."""
    candidates = [
        (By.ID, "buttonFiel"),
        (By.XPATH, "//*[self::a or self::button or self::div or self::span or self::label]"
                 + "[contains(translate(.,'ÉÍÓÚÁéíóúá','EIOUAeioua'),'E.FIRMA') or contains(.,'e.firma') or contains(.,'eFirma')]"),
        (By.XPATH, "//a[contains(@class,'nav-link') and contains(translate(.,'E.FIRMA','e.firma'),'e.firma')]"),
    ]

    for locator in candidates:
        elements = driver.find_elements(*locator)
        if elements:
            efirma_btn = elements[0]

            try:
                efirma_btn.click()
                sleep(1)
                print(f" -> E.firma seleccionada por locator {locator}.")
                return
            except Exception:
                driver.execute_script("arguments[0].click();", efirma_btn)
                sleep(1)
                print(f" -> E.firma seleccionada por locator {locator} (JS).")
                return
    
    if click_by_inner_text_js(driver, ["e.firma", "efirma", "firma", "certificado"]):
        sleep(1)
        print(" -> E.firma seleccionada por texto visible (JS).")
        return

    raise NoSuchElementException("No se pudo localizar ni hacer click en la pestaña/botón 'e.firma'.")

def make_file_input_visible(driver: webdriver.chrome.webdriver.WebElement, el: webdriver.remote.webelement.WebElement):
    """Hace visible un input[type='file'] para poder enviar la ruta directamente (Workaround de Selenium)."""
    js = """
        arguments[0].style.display='block';
        arguments[0].style.visibility='visible';
        arguments[0].removeAttribute('disabled');
        arguments[0].removeAttribute('readonly');
        arguments[0].style.opacity='1';
        arguments[0].style.position='fixed';
        arguments[0].style.zIndex='99999';
        """
    driver.execute_script(js, el)

def upload_file_to_any(driver: webdriver.Chrome, locators: List[tuple], absolute_path: str) -> bool:
    """Intenta subir el archivo a cualquiera de los locators dados."""
    for locator in locators:
        elements = driver.find_elements(*locator)
        if elements:
            input_el = elements[0]
            try:
                make_file_input_visible(driver, input_el)
                input_el.send_keys(absolute_path)
                sleep(0.3)
                return True
            except Exception:
                pass
    return False

def upload_efirma_files(driver: webdriver.Chrome, cer_path: str, key_path: str):
    """Carga los archivos .cer y .key."""
    cer = Path(cer_path).resolve()
    key = Path(key_path).resolve()

    if not cer.exists() or not key.exists():
        # Usar la excepción nativa de Python
        raise FileNotFoundError(
            f"Rutas de e.firma inválidas o inaccesibles: {cer_path} / {key_path}"
        )

    cer_locators = [
        (By.CSS_SELECTOR, "input[type='file'][accept*='.cer' i]"),
        (By.ID, "fileCer"), (By.NAME, "fileCer"),
        (By.XPATH, "//label[contains(translate(normalize-space(.),'CERTIFICADO','certificado'),'CERTIFICADO')]/following::input[@type='file'][1]")
    ]

    key_locators = [
        (By.CSS_SELECTOR, "input[type='file'][accept*='.key' i]"),
        (By.ID, "fileKey"), (By.NAME, "fileKey"),
        (By.XPATH, "//label[contains(translate(normalize-space(.),'LLAVE PRIVADA','llave privada'),'LLAVE PRIVADA')]/following::input[@type='file'][1]"),
        (By.XPATH, "//input[@type='file'][not(@value)]")
    ]

    # Subir .cer (con búsqueda en iframes)
    if not upload_file_to_any(driver, cer_locators, str(cer)):
        uploaded = False
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for frame in iframes:
            try:
                driver.switch_to.frame(frame)
                if upload_file_to_any(driver, cer_locators, str(cer)):
                    uploaded = True
                    driver.switch_to.default_content()
                    break
            except Exception:
                pass
            finally:
                driver.switch_to.default_content()
        
        if not uploaded:
            raise NoSuchElementException("No se pudo subir el archivo .cer. No se encontró el input 'file'.")

    # Subir .key (con búsqueda en iframes)
    if not upload_file_to_any(driver, key_locators, str(key)):
        uploaded = False
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for frame in iframes:
            try:
                driver.switch_to.frame(frame)
                if upload_file_to_any(driver, key_locators, str(key)):
                    uploaded = True
                    driver.switch_to.default_content()
                    break
            except Exception:
                pass
            finally:
                driver.switch_to.default_content()
        
        if not uploaded:
            raise NoSuchElementException("No se pudo subir el archivo .key. No se encontró el input 'file'.")

def enter_key_password_and_sign(driver: webdriver.Chrome, key_password: str):
    """Ingresa la contraseña y hace clic en el botón de Firmar/Enviar."""
    switch_to_login_frame_if_any(driver)

    pwd_locators = [
        (By.CSS_SELECTOR, "input[type='password']"),
        (By.ID, "contrasena"), (By.NAME, "contrasena"),
        (By.XPATH, "//label[contains(translate(.,'ÁÉÍÓÚáéíóú','AEIOUaeiou'),'CONTRASENA')]/following::input[@type='password'][1]")
    ]

    pwd = find_first_present(driver, *pwd_locators)
    if pwd is None:
        raise NoSuchElementException("No encontré el campo de contraseña de la e.firma.")

    pwd.clear()
    pwd.send_keys(key_password)

    sign_btn_locators = [
        (By.XPATH, "//button[contains(translate(.,'ENVIAR','enviar'),'enviar')]"),
        (By.XPATH, "//input[@type='submit' or @type='button'][contains(translate(@value,'ENVIAR','enviar'),'enviar')]"),
        (By.ID, "btnFirma"), (By.NAME, "btnFirma"),
        (By.XPATH, "//button[contains(.,'Firmar') or contains(.,'Ingresar') or contains(.,'Acceder')]"),
    ]

    sign_btn = find_first_clickable(driver, *sign_btn_locators)

    if sign_btn is None:
        raise NoSuchElementException("No encontré el botón para firmar con e.firma (Firmar/Enviar).")

    sign_btn.click()
    sleep(2)


# =======================================================
# 4. UTILIDADES DE DESCARGA
# =======================================================

def snapshot_filenames(directory: Path) -> Set[str]:
    """Obtiene los nombres de los archivos en un directorio."""
    try:
        return {p.name for p in directory.iterdir() if p.is_file()}
    except FileNotFoundError:
        return set()
    except Exception:
        return set()

def wait_for_new_pdf_download(download_dir: Path, known_files: Set[str], timeout_seconds: float) -> Optional[Path]:
    """Espera a que un nuevo archivo PDF aparezca en el directorio de descarga."""
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        current_files = snapshot_filenames(download_dir)
        new_files = current_files - known_files

        for name in new_files:
            # Si termina en .pdf y NO es un archivo de descarga parcial de Chrome (.crdownload)
            if name.lower().endswith(".pdf") and not name.endswith(".crdownload"):
                new_path = download_dir / name
                sleep(1) 
                return new_path

        sleep(1)
        
    return None


# =======================================================
# 5. FUNCIÓN PRINCIPAL DE AUTOMATIZACIÓN (CORE)
# =======================================================

def run_sat_automation_core(cer_path: str, key_path: str, key_pass: str, download_dir: Path) -> Path:
    """Función de automatización de Selenium para el SAT."""
    final_pdf_path = None
    main_handle = None
    driver = None

    try:
        # Configuración de Chrome Options
        download_dir.mkdir(parents=True, exist_ok=True)
        
        prefs = {
            "download.prompt_for_download": False,
            "download.default_directory": str(download_dir.resolve()),
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True, # Desactiva el visor de PDF de Chrome
        }

        opts = Options()
        opts.add_experimental_option("prefs", prefs)
        opts.add_argument("--window-size=1366,900")
        opts.add_argument("--disable-popup-blocking")
        
        # Opciones Headless (se recomienda para entornos de servidor)
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        
        # Inicializar WebDriver
        try:
            driver = webdriver.Chrome(options=opts)
        except WebDriverException as e:
            # Captura errores de inicialización (e.g., ChromeDriver no encontrado)
            raise RuntimeError(f"Error al inicializar WebDriver: {e}")
            
        driver.implicitly_wait(0)
        wait = WebDriverWait(driver, TIMEOUT_DURATION_SECONDS)

        # 1) Navegar a la página de login
        try:
            driver.get("https://wwwmat.sat.gob.mx/aplicacion/login/53027/genera-tu-constancia-de-situacion-fiscal")
            wait.until(lambda d: "login" in d.current_url or "nidp" in d.current_url)
        except TimeoutException:
            driver.get("https://wwwmat.sat.gob.mx/aplicacion/53027/genera-tu-constancia-de-situacion-fiscal")
            ejecutar = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(.,'Ejecutar en línea') or contains(.,'Ejecutar en linea')]"))
            )
            ejecutar.click()
            wait.until(lambda d: "login" in d.current_url or "nidp" in d.current_url)

        # 2) Entrar a iframe de login
        switch_to_login_frame_if_any(driver)

        # 3) Seleccionar e.firma
        print("Intentando seleccionar e.firma...")
        select_efirma_tab(driver)
        sleep(1.5)
        switch_to_login_frame_if_any(driver)

        # 4) Cargar .cer y .key
        print("Cargando archivos .cer y .key...")
        upload_efirma_files(driver, cer_path, key_path)

        # 5) Contraseña de la llave y firmar
        print("Ingresando contraseña y firmando...")
        enter_key_password_and_sign(driver, key_pass)

        # 6) Esperar retorno al módulo
        wait.until(lambda d: "genera-tu-constancia-de-situacion-fiscal" in d.current_url)
        print("¡Inicio de sesión con e.firma exitoso!")

        # 6.5) Scroll horizontal
        print("Realizando scroll horizontal hacia la derecha para localizar 'Generar Constancia'...")
        scroll_horizontal_all_the_way(driver)
        sleep(1)

        # 7) HACER CLIC EN GENERAR CONSTANCIA
        main_handle = driver.current_window_handle
        click_generar_constancia_btn(driver)
        print("✅ Botón 'Generar Constancia' presionado.")

        # 7.5) MANEJO DE NUEVA VENTANA / PESTAÑA DEL PDF
        print("Esperando que se abra la pestaña con la constancia (hasta 15 s)...")
        
        # Función auxiliar para encontrar el nuevo handle
        def get_new_handle(driver, main_handle):
            handles = driver.window_handles
            if len(handles) > 1:
                return next((h for h in handles if h != main_handle), None)
            return None

        pdf_handle = WebDriverWait(driver, 15).until(lambda d: get_new_handle(d, main_handle))

        if pdf_handle:
            driver.switch_to.window(pdf_handle)
            print(f" -> Cambiado a pestaña del PDF: {driver.current_url}")
        else:
            driver.switch_to.window(main_handle)
            print(f" -> Seguimos en la ventana principal: {driver.current_url}")

        # 8) OBTENER EL PDF POR DESCARGA AUTOMÁTICA
        print("Iniciando espera de la descarga automática del PDF (máx 120 segundos)...")
        before_files = snapshot_filenames(download_dir)

        new_file = wait_for_new_pdf_download(download_dir, before_files, 120)

        if new_file:
            final_pdf_path = download_dir / DEFAULT_FINAL_PDF_NAME
            if final_pdf_path.exists():
                final_pdf_path.unlink() # Borrar el archivo si ya existe
            
            new_file.rename(final_pdf_path) # Mover/renombrar
            
            print(f" -> PDF detectado por descarga automática en: {final_pdf_path.resolve()}")
            return final_pdf_path
        else:
            raise TimeoutException("No se detectó la descarga automática del PDF en 120 segundos.")

    except Exception as e:
        # Relanzar la excepción para que el main la maneje
        raise e
        
    finally:
        if driver:
            # Lógica de cierre de ventanas/pestañas
            try:
                handles = driver.window_handles
                if main_handle and len(handles) > 1 and driver.current_window_handle != main_handle:
                    driver.close()
                    driver.switch_to.window(main_handle)
            except Exception:
                pass
            
            driver.quit()


# =======================================================
# 6. MÉTODO MAIN (EJECUCIÓN)
# =======================================================

def main():
    """Método principal para la ejecución del script."""
    # El directorio de descarga se crea en la carpeta de ejecución
    download_dir = Path.cwd() / "constancias"

    try:
        pdf_path = run_sat_automation_core(
            str(DEFAULT_CER_PATH), 
            str(DEFAULT_KEY_PATH),
            DEFAULT_KEY_PASS,
            download_dir
        )

        print("\n--- RESULTADO ---")
        print("Status: SUCCESS")
        print("Mensaje: Constancia generada y guardada.")
        print(f"PDF en: {pdf_path.resolve()}")

    except Exception as e:
        print("\n--- ERROR ---")
        
        detail = "Fallo desconocido en la automatización."
        
        if isinstance(e, NoSuchElementException):
            detail = f"Error al localizar un elemento: {e}. El portal SAT pudo haber cambiado su estructura (DOM)."
        elif isinstance(e, TimeoutException):
            detail = f"Tiempo de espera agotado (Timeout de Selenium): {e.msg if hasattr(e, 'msg') else str(e)}"
        elif isinstance(e, FileNotFoundError):
            detail = f"Error en ruta de e.firma: {e}. Verifique que las rutas absolutas sean correctas y que los archivos existan."
        elif isinstance(e, RuntimeError) and "WebDriver" in str(e):
             detail = f"Error de inicialización de Selenium/Chrome: {e}. Asegúrese de que Google Chrome esté instalado y el ChromeDriver esté disponible (o que el driver esté en el PATH)."
        else:
             detail = f"Fallo inesperado: {type(e).__name__}: {e}"

        print(f"Status: FALLO\nDetalle: {detail}")

if __name__ == "__main__":
    main()
