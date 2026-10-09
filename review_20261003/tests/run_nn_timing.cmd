@echo off
call "E:\Software_Download\VS2017\VC\Auxiliary\Build\vcvars64.bat" >nul
if not "%errorlevel%"=="0" exit /b %errorlevel%
cl /nologo /utf-8 /TC /O2 /W3 /wd4068 /wd4305 /wd4101 /fp:strict /D_CRT_SECURE_NO_WARNINGS /Dinline=__inline /DDAB_BOARD_CONFIG_CONFIRMED=1 /I"tests\stubs" /I"..\dab_control_f28p550" tests\test_nn_timing.c tests\mock_driver.c ..\dab_control_f28p550\dab_adc.c ..\dab_control_f28p550\dab_control.c ..\dab_control_f28p550\dab_nn.c ..\dab_control_f28p550\dab_protect.c ..\dab_control_f28p550\dab_pwm.c ..\dab_control_f28p550\dab_telemetry.c /Fe:tests\test_nn_timing.exe
if errorlevel 1 exit /b %errorlevel%
tests\test_nn_timing.exe
if errorlevel 1 exit /b %errorlevel%
cl /nologo /utf-8 /TC /W3 /wd4068 /wd4305 /wd4101 /fp:strict /Dinline=__inline /DDAB_USE_HARDWARE_NPU /DDAB_NPU_FLOAT_IO_CONFIRMED /I"tests\stubs" /I"..\dab_control_f28p550" tests\test_nn_npu_timing.c tests\mock_driver.c ..\dab_control_f28p550\dab_nn.c /Fe:tests\test_nn_npu_timing.exe
if errorlevel 1 exit /b %errorlevel%
tests\test_nn_npu_timing.exe
exit /b %errorlevel%
