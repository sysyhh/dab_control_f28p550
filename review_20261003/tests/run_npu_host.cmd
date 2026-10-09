@echo off
call "E:\Software_Download\VS2017\VC\Auxiliary\Build\vcvars64.bat" >nul
if not "%errorlevel%"=="0" exit /b %errorlevel%
cl /nologo /utf-8 /TC /W3 /wd4068 /wd4305 /wd4101 /fp:strict /Dinline=__inline /DDAB_USE_HARDWARE_NPU /DDAB_NPU_FLOAT_IO_CONFIRMED /I"tests\stubs" /I"..\dab_control_f28p550" tests\test_npu_service.c tests\mock_driver.c ..\dab_control_f28p550\dab_nn.c /Fe:tests\test_npu_service.exe
if not "%errorlevel%"=="0" exit /b %errorlevel%
tests\test_npu_service.exe
exit /b %errorlevel%
