# 🇲🇽 SAT Constancia de Situación Fiscal - Automatización con e.firma

**Obtén automáticamente la Constancia de Situación Fiscal del SAT (México) utilizando Selenium, Python y tu e.firma (FIEL).**

---

## 💡 Sobre el Proyecto

Este script de Python automatiza el tedioso proceso de iniciar sesión en el portal del SAT (Servicio de Administración Tributaria) utilizando los archivos de la **e.firma** (`.cer`, `.key`, contraseña) y navega hasta el módulo de generación de la Constancia de Situación Fiscal, manejando la descarga automática del PDF.

> **Advertencia:** La estructura del portal SAT cambia frecuentemente. Si el script falla, es probable que los selectores de Selenium deban ser actualizados.

## ⚙️ Requisitos

1.  **Python 3.8+**
2.  **Google Chrome** instalado (el script utiliza `webdriver.Chrome`).
3.  Tener tus archivos de **e.firma (.cer, .key y contraseña)** a la mano.

## 🚀 Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/tu-usuario/sat-constancia-efirma-selenium.git](https://github.com/tu-usuario/sat-constancia-efirma-selenium.git)
    cd sat-constancia-efirma-selenium
    ```

2.  **Crear y activar un entorno virtual (recomendado):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Linux/macOS
    venv\Scripts\activate     # En Windows
    ```

3.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(Opcional pero recomendado)** **Configurar Credenciales:**
    Crea un archivo llamado `.env` en la raíz del proyecto para almacenar tus credenciales y rutas de forma segura.

    ```bash
    # .env
    CER_PATH="C:/ruta/absoluta/a/tu/certificado.cer"
    KEY_PATH="C:/ruta/absoluta/a/tu/claveprivada.key"
    KEY_PASS="Tu_Contraseña_Secreta"
    ```
    *Asegúrate de no subir este archivo a Git.*

## 🏃 Uso

El script principal es `sat_constancia_core.py`. Asegúrate de que las rutas dentro del script o en tu archivo de configuración sean las correctas.

1.  **Ejecutar el script:**
    ```bash
    python main.py
    ```
    *(Si usaste la versión CLI con el bloque `if __name__ == "__main__":`)*

2.  **Revisa la salida:**
    El script imprimirá el estado de la automatización. Si es exitosa, el PDF se guardará en un subdirectorio llamado `constancias/` dentro del proyecto.

    ```
    ...
    ¡Inicio de sesión con e.firma exitoso!
    ✅ Botón 'Generar Constancia' presionado.
    Iniciando espera de la descarga automática del PDF (máx 120 segundos)...
    
    --- RESULTADO ---
    Status: SUCCESS
    Mensaje: Constancia generada y guardada.
    PDF en: /ruta/al/proyecto/constancias/constancia_sat.pdf
    ```

## 🚨 Manejo de Errores Comunes

| Error | Causa Probable | Solución |
| :--- | :--- | :--- |
| `NoSuchElementException` | El SAT cambió el ID o el XPATH de un botón o campo. | Debes inspeccionar el portal del SAT y actualizar los selectores en `sat_constancia_core.py`. |
| `FileNotFoundError` | La ruta al archivo `.cer` o `.key` es incorrecta o los archivos no existen. | Verifica las rutas absolutas en la sección de configuración. |
| `TimeoutException` | El inicio de sesión tardó demasiado, el botón no apareció, o el SAT pudo haber solicitado un Captcha. | Intenta correr el script sin modo `headless` (`--headless=new`) para ver dónde se detiene la ejecución. |
| `WebDriverException` | El ChromeDriver no se encontró o no es compatible con tu versión de Chrome. | Asegúrate de tener Google Chrome actualizado y verifica que el `chromedriver` esté accesible desde tu PATH. |

---

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Si encuentras un error o necesitas actualizar los selectores debido a un cambio en el portal del SAT, por favor:

1.  Haz un "Fork" de este repositorio.
2.  Crea una nueva rama (`git checkout -b feature/actualizar-selectores`).
3.  Realiza tus cambios y haz commit (`git commit -m 'feat: actualizar selectores de login del SAT'`).
4.  Push a la rama (`git push origin feature/actualizar-selectores`).
5.  Crea un nuevo Pull Request.
