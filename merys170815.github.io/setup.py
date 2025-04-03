from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


driver = webdriver.Chrome()  # O reemplaza con el navegador que uses
url = "https://qxbroker.com/es"
driver.get(url)


# Increase wait timeout if necessary
wait = WebDriverWait(driver, 20)  # Ajusta el tiempo de espera en segundos

try:
    email_field = wait.until(EC.presence_of_element_located((By.ID, "email_field_id")))  # Reemplaza con ID real (inspecciona la página)
    password_field = wait.until(EC.presence_of_element_located((By.ID, "password_field_id")))  # Reemplaza con ID real
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "login_button_id")))  # Reemplaza con ID real o By.NAME si aplica
except TimeoutException:
    print("Elementos no encontrados dentro del tiempo de espera.")
    driver.quit()
    exit()  # Opcional para detener la ejecución

    # Enter email and password
    email_field.send_keys("sirem66@gmail.com")
    password_field.send_keys("22520873Me")
    login_button.click()

except Exception as e:
    print(f"Ocurrió un error: {e}")


driver.quit()

