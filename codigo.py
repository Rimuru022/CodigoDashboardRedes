import machine 

import utime 

import network 

import socket 

import ujson 

import gc 

from machine import Pin, ADC 

 

# Forzar liberación de memoria desde el inicio 

gc.collect() 

 

# Configuración básica 

led = Pin("LED", Pin.OUT) 

sensor_power = Pin(15, Pin.OUT) 

sensor_temp = ADC(26) 

sensor_humedad = ADC(27) 

 

# Almacenamiento de datos 

MAX_DATOS = 20 

datos_temperatura = [] 

datos_humedad = [] 

timestamps = [] 

 

# ========== CORRECCIÓN PARA TEMPERATURA INVERTIDA Y FACTOR DE CALIBRACIÓN =========== 

CORREGIR_INVERSION_TEMP = True  # Activa la corrección de inversión 

OFFSET_TEMPERATURA = 1.0  # Ajuste fino si es necesario 

FACTOR_CALIBRACION_TEMP = 0.48  # Reduce las lecturas aproximadamente a la mitad 

 

def leer_temperatura(): 

    """Lee temperatura con corrección para lecturas invertidas y factor de calibración""" 

    # Encender sensor brevemente 

    sensor_power.value(1) 

    utime.sleep_ms(200) 

     

    # Tomar múltiples lecturas para estabilidad 

    total = 0 

    muestras = 5  # Más muestras para mayor estabilidad 

    for _ in range(muestras): 

        total += sensor_temp.read_u16() 

        utime.sleep_ms(20) 

     

    # Apagar sensor 

    sensor_power.value(0) 

     

    # Cálculo base 

    promedio = total / muestras 

    voltaje = (promedio / 65535) * 3.3 

     

    # CORRECCIÓN para valores invertidos 

    if CORREGIR_INVERSION_TEMP: 

        # Método 1: Si el sensor está invirtiendo las lecturas (de 0°C a 100°C) 

        temperatura = (100 - (voltaje * 100)) + OFFSET_TEMPERATURA 

    else: 

        # Método estándar LM35 

        temperatura = (voltaje * 100) + OFFSET_TEMPERATURA 

     

    # AÑADIDO: Aplicar factor de calibración para ajustar la lectura 

    temperatura = temperatura * FACTOR_CALIBRACION_TEMP 

     

    # Validación de rango 

    if temperatura < 0 or temperatura > 50: 

        # Valor fuera de rango esperado - usar último válido o default 

        if datos_temperatura: 

            return datos_temperatura[-1]  # Usar último valor válido 

        return 20.0  # Valor por defecto si no hay histórico 

     

    return round(temperatura, 1) 

 

def leer_humedad(): 

    """Lee humedad del suelo con mayor estabilidad""" 

    # Tomar múltiples lecturas 

    total = 0 

    muestras = 3 

    for _ in range(muestras): 

        total += sensor_humedad.read_u16() 

        utime.sleep_ms(10) 

     

    valor_adc = total / muestras 

     

    # Calibración - ajustar estos valores según tu sensor 

    valor_seco = 60000  # Ajustar según tus pruebas 

    valor_mojado = 25000  # Ajustar según tus pruebas 

     

    # Limitar valores dentro del rango esperado 

    if valor_adc > valor_seco: 

        valor_adc = valor_seco 

    if valor_adc < valor_mojado: 

        valor_adc = valor_mojado 

     

    # Calcular porcentaje 

    humedad = ((valor_seco - valor_adc) * 100) / (valor_seco - valor_mojado) 

     

    # Validar rango 

    humedad = max(0, min(100, humedad)) 

     

    return round(humedad, 1) 

 

# ========== MEJORA DE CONEXIÓN WIFI ========== 

def conectar_wifi(): 

    """Conexión WiFi optimizada para evitar errores""" 

    ssid = "POCO F5 Pro" 

    password = "Ivan1234" 

     

    print("Iniciando conexión WiFi...") 

     

    # Desconectar cualquier intento previo 

    wlan = network.WLAN(network.STA_IF) 

    wlan.active(False) 

    utime.sleep(1) 

    wlan.active(True) 

     

    # Configurar modo de ahorro de energía desactivado para evitar timeouts 

    wlan.config(pm = 0xa11140)  # Desactivar ahorro de energía 

     

    # Intentar conexión 

    print(f"Conectando a {ssid}...") 

    wlan.connect(ssid, password) 

     

    # Esperar con timeout y feedback visual 

    max_espera = 20 

    while max_espera > 0: 

        if wlan.isconnected(): 

            break 

        max_espera -= 1 

        led.toggle() 

        print(".", end="") 

        utime.sleep(1) 

     

    print("") 

     

    # Verificar resultado 

    if wlan.isconnected(): 

        ip = wlan.ifconfig()[0] 

        print(f"¡WiFi conectado! IP: {ip}") 

        led.on() 

        return ip 

    else: 

        print("Error de conexión WiFi") 

        led.off() 

        return None 

 

# ========== HTML SIMPLIFICADO PERO COMPLETO ========== 

def html_pagina(): 

    """HTML con mejor rendimiento y estabilidad""" 

    return """<!DOCTYPE html> 

<html> 

<head> 

    <meta charset="UTF-8"> 

    <meta name="viewport" content="width=device-width, initial-scale=1.0"> 

    <title>Monitor Ambiental</title> 

    <style> 

        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; } 

        .container { max-width: 800px; margin: 20px auto; padding: 10px; } 

        .header { background: #2c3e50; color: white; padding: 15px; text-align: center; border-radius: 4px; } 

        .reading-box { display: flex; justify-content: space-around; margin: 20px 0; } 

        .reading { text-align: center; padding: 15px; border-radius: 4px; background: white; box-shadow: 0 2px 5px rgba(0,0,0,0.1); width: 45%; } 

        .value { font-size: 2.5rem; font-weight: bold; margin: 10px 0; } 

        .temp { color: #e74c3c; } 

        .hum { color: #3498db; } 

        .chart-box { background: white; padding: 15px; margin: 20px 0; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); } 

        .status-bar { display: flex; justify-content: space-between; align-items: center; padding: 10px; background: white; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); } 

        button { background: #3498db; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; } 

        button:hover { background: #2980b9; } 

    </style> 

</head> 

<body> 

    <div class="container"> 

        <div class="header"> 

            <h1>Monitor de Temperatura y Humedad</h1> 

        </div> 

         

        <div class="reading-box"> 

            <div class="reading"> 

                <h2>Temperatura</h2> 

                <div class="value temp" id="temp">--</div> 

                <div>°C</div> 

            </div> 

            <div class="reading"> 

                <h2>Humedad</h2> 

                <div class="value hum" id="hum">--</div> 

                <div>%</div> 

            </div> 

        </div> 

         

        <div class="chart-box"> 

            <canvas id="chart" height="250"></canvas> 

        </div> 

         

        <div class="status-bar"> 

            <div id="time">--</div> 

            <button onclick="actualizarDatos()">Actualizar</button> 

        </div> 

    </div> 

 

    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script> 

    <script> 

        // Chart global 

        let myChart; 

        let lastUpdateTime = 0; 

         

        // Inicializar gráfico 

        function iniciarGrafico() { 

            const ctx = document.getElementById('chart').getContext('2d'); 

            myChart = new Chart(ctx, { 

                type: 'line', 

                data: { 

                    labels: [], 

                    datasets: [ 

                        { 

                            label: 'Temperatura (°C)', 

                            data: [], 

                            borderColor: '#e74c3c', 

                            backgroundColor: 'rgba(231,76,60,0.1)', 

                            borderWidth: 2, 

                            fill: true, 

                            tension: 0.3 

                        }, 

                        { 

                            label: 'Humedad (%)', 

                            data: [], 

                            borderColor: '#3498db', 

                            backgroundColor: 'rgba(52,152,219,0.1)', 

                            borderWidth: 2, 

                            fill: true, 

                            tension: 0.3 

                        } 

                    ] 

                }, 

                options: { 

                    responsive: true, 

                    maintainAspectRatio: false, 

                    interaction: { 

                        mode: 'index', 

                        intersect: false 

                    }, 

                    scales: { 

                        y: { 

                            beginAtZero: false 

                        } 

                    }, 

                    animation: { 

                        duration: 0  // Desactivar animaciones para mejor rendimiento 

                    } 

                } 

            }); 

        } 

         

        // Actualizar datos con límite de frecuencia para evitar sobrecargar 

        function actualizarDatos(forzar = false) { 

            const ahora = Date.now(); 

             

            // Evitar muchas actualizaciones seguidas (a menos que sea forzada) 

            if (!forzar && (ahora - lastUpdateTime < 5000)) { 

                return; 

            } 

             

            // Actualizar tiempo 

            lastUpdateTime = ahora; 

            document.getElementById('time').textContent = 'Actualizando...'; 

             

            // Petición con timeout corto 

            const controller = new AbortController(); 

            const timeoutId = setTimeout(() => controller.abort(), 4000); 

             

            fetch('/datos', { signal: controller.signal }) 

                .then(response => response.json()) 

                .then(data => { 

                    // Actualizar valores actuales 

                    document.getElementById('temp').textContent = data.temperatura_actual; 

                    document.getElementById('hum').textContent = data.humedad_actual; 

                     

                    // Actualizar gráfico 

                    if (myChart) { 

                        myChart.data.labels = data.timestamps; 

                        myChart.data.datasets[0].data = data.temperaturas; 

                        myChart.data.datasets[1].data = data.humedades; 

                        myChart.update('none'); 

                    } 

                     

                    // Actualizar estado 

                    const now = new Date(); 

                    document.getElementById('time').textContent = 'Última actualización: ' + now.toLocaleTimeString(); 

                     

                    // Programar próxima actualización automática con intervalo más largo 

                    setTimeout(() => actualizarDatos(), 8000); 

                }) 

                .catch(error => { 

                    console.error('Error:', error); 

                    document.getElementById('time').textContent = 'Error de conexión'; 

                    setTimeout(() => actualizarDatos(), 15000); 

                }) 

                .finally(() => { 

                    clearTimeout(timeoutId); 

                }); 

        } 

         

        // Iniciar aplicación 

        window.addEventListener('load', function() { 

            iniciarGrafico(); 

            actualizarDatos(true); 

        }); 

    </script> 

</body> 

</html> 

""" 

 

# ========== SERVIDOR OPTIMIZADO CONTRA TIMEOUTS ========== 

def iniciar_servidor(ip): 

    """Servidor web optimizado contra errores de timeout""" 

    puerto = 80  # Puerto estándar HTTP 

     

    # Crear socket con configuración optimizada 

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

     

    try: 

        # Configurar socket 

        servidor.bind((ip, puerto)) 

        servidor.listen(1) 

        print(f"Servidor web iniciado en http://{ip}") 

         

        # Lectura inicial 

        temp = leer_temperatura() 

        hum = leer_humedad() 

        hora = "{:02d}:{:02d}".format(utime.localtime()[3], utime.localtime()[4]) 

         

        # Guardar primera lectura 

        datos_temperatura.append(temp) 

        datos_humedad.append(hum) 

        timestamps.append(hora) 

         

        print(f"Primera lectura - Temp: {temp}°C, Humedad: {hum}%") 

         

        # Variables de control 

        ultima_lectura = utime.time() 

        intervalo_lectura = 5  # Intervalo más largo para mayor estabilidad 

         

        # Bucle principal optimizado para evitar bloqueos 

        while True: 

            # Tomar lecturas según intervalo 

            tiempo_actual = utime.time() 

            if tiempo_actual - ultima_lectura >= intervalo_lectura: 

                # Leer sensores 

                try: 

                    temp = leer_temperatura() 

                    hum = leer_humedad() 

                    hora = "{:02d}:{:02d}".format(utime.localtime()[3], utime.localtime()[4]) 

                     

                    # Guardar datos 

                    datos_temperatura.append(temp) 

                    datos_humedad.append(hum) 

                    timestamps.append(hora) 

                     

                    # Limitar tamaño para evitar desbordamiento de memoria 

                    if len(datos_temperatura) > MAX_DATOS: 

                        datos_temperatura.pop(0) 

                        datos_humedad.pop(0) 

                        timestamps.pop(0) 

                     

                    # Actualizar 

                    print(f"Lectura - Temp: {temp}°C, Humedad: {hum}%") 

                    ultima_lectura = tiempo_actual 

                    led.toggle() 

                     

                    # Liberar memoria 

                    gc.collect() 

                except Exception as e: 

                    print(f"Error en lectura: {e}") 

             

            # Esperar conexiones con timeout corto 

            try: 

                # Timeout más corto para no bloquear otras operaciones 

                servidor.settimeout(0.1) 

                conn, addr = servidor.accept() 

                 

                # Establecer timeout para evitar conexiones bloqueadas 

                conn.settimeout(2.0) 

                 

                try: 

                    # Procesar solicitud con timeout estricto 

                    request = conn.recv(1024).decode('utf-8') 

                     

                    if request.find('GET /datos') == 0: 

                        # Preparar datos JSON 

                        datos = { 

                            'temperatura_actual': datos_temperatura[-1] if datos_temperatura else 0, 

                            'humedad_actual': datos_humedad[-1] if datos_humedad else 0, 

                            'temperaturas': datos_temperatura, 

                            'humedades': datos_humedad, 

                            'timestamps': timestamps 

                        } 

                         

                        # Generar JSON simple 

                        try: 

                            json_data = ujson.dumps(datos) 

                        except: 

                            json_data = '{"error": "Error de datos"}' 

                         

                        # Enviar respuesta compacta 

                        respuesta = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n" 

                        respuesta += "Connection: close\r\nAccess-Control-Allow-Origin: *\r\n" 

                        respuesta += f"Content-Length: {len(json_data)}\r\n\r\n" 

                        respuesta += json_data 

                         

                        # Enviar en bloques si es grande para evitar bloqueos 

                        try: 

                            conn.sendall(respuesta.encode('utf-8')) 

                        except: 

                            print("Error al enviar datos JSON") 

                    else: 

                        # Página HTML principal 

                        html = html_pagina() 

                         

                        # Enviar respuesta HTML 

                        respuesta = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n" 

                        respuesta += "Connection: close\r\n" 

                        respuesta += f"Content-Length: {len(html)}\r\n\r\n" 

                        respuesta += html 

                         

                        # Enviar HTML en bloques si es grande 

                        try: 

                            conn.sendall(respuesta.encode('utf-8')) 

                        except: 

                            print("Error al enviar HTML") 

                             

                except Exception as e: 

                    print(f"Error procesando solicitud: {e}") 

                 

                # Cerrar conexión de inmediato 

                try: 

                    conn.close() 

                except: 

                    pass 

                     

            except OSError: 

                # Timeout esperado del socket, continuar 

                pass 

             

    except Exception as e: 

        print(f"Error del servidor: {e}") 

    finally: 

        # Limpiar recursos 

        try: 

            servidor.close() 

        except: 

            pass 

        print("Servidor detenido") 

 

def main(): 

    print("=== Sistema de Monitoreo Ambiental ===") 

    print("Iniciando sistema...") 

     

    # Configuración inicial 

    sensor_power.value(0)  # Sensor apagado por defecto 

     

    while True: 

        # Conectar WiFi con reintento automático 

        ip = conectar_wifi() 

         

        if ip: 

            try: 

                iniciar_servidor(ip) 

            except Exception as e: 

                print(f"Error crítico: {e}") 

                print("Reiniciando sistema en 5 segundos...") 

                utime.sleep(5) 

        else: 

            print("No se pudo conectar al WiFi. Reintentando en 10 segundos...") 

            utime.sleep(10) 

 

if __name__ == "__main__": 

    main() 