(CURSO\venv - Python 3.14.8) PS D:\DiscoX\GIT\CURSO\src\Bloque_14> pytest test_cliente.py -v


==================================================== test session starts =====================================================
platform win32 -- Python 3.15.2, pytest-9.2.0, pluggy-1.7.0 -- D:\DiscoX\GIT\CURSO\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\DiscoX\GIT\CURSO\src\Bloque_14
collected 9 items

test_cliente.py::test_enviar_peticion_credencial_invalida PASSED                                                        [ 11%]
test_cliente.py::test_enviar_peticion_limite_de_uso PASSED                                                              [ 22%]
test_cliente.py::test_enviar_peticion_exito PASSED                                                                      [ 33%]
test_cliente.py::test_con_reintento_espera_entre_intentos PASSED                                                        [ 44%]
test_cliente.py::test_con_reintento_agota_intentos PASSED                                                               [ 55%]
test_cliente.py::test_con_reintento_no_reintenta_value_error PASSED                                                     [ 66%]
test_cliente.py::test_calcular_costo PASSED                                                                             [ 77%]
test_cliente.py::test_consultar_modelo_convierte_error PASSED                                                           [ 88%]
test_cliente.py::test_consultar_modelo_acumula_costo PASSED                                                             [100%]

===================================================== 9 passed in 0.18s ======================================================




