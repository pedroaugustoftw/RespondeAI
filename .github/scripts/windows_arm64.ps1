param([ValidateSet('geometry','opencv')][string]$Stage)
$ErrorActionPreference = 'Stop'
$geosPrefix = Join-Path $PWD 'build-geos-install'
if ($Stage -eq 'geometry') {
if (-not (Test-Path (Join-Path $geosPrefix 'bin\geos_c.dll'))) {
git clone --depth 1 --branch 3.13.1 https://github.com/libgeos/geos.git build-geos-source
if ($LASTEXITCODE) { throw 'Falha ao baixar GEOS' }
cmake -S build-geos-source -B build-geos -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_INSTALL_PREFIX=$geosPrefix" -DBUILD_TESTING=OFF -DBUILD_DOCUMENTATION=OFF
if ($LASTEXITCODE) { throw 'Falha ao configurar GEOS' }
cmake --build build-geos --config Release --parallel 4
if ($LASTEXITCODE) { throw 'Falha ao compilar GEOS' }
cmake --install build-geos --config Release
if ($LASTEXITCODE) { throw 'Falha ao instalar GEOS' }
}
$env:GEOS_INCLUDE_PATH = Join-Path $geosPrefix 'include'
$env:GEOS_LIBRARY_PATH = Join-Path $geosPrefix 'lib'
$env:PATH = (Join-Path $geosPrefix 'bin') + ';' + $env:PATH
python -m pip install --only-binary=numpy numpy cython setuptools wheel ninja cmake scikit-build
if ($LASTEXITCODE) { throw 'Falha nas ferramentas de compilacao' }
python -m pip install --no-binary=shapely,pyclipper shapely pyclipper
if ($LASTEXITCODE) { throw 'Falha ao compilar Shapely/pyclipper' }
# DLLs junto do modulo para que o carregador e o PyInstaller as encontrem.
$shapelyFolder = python -c "import importlib.util,pathlib; print(pathlib.Path(importlib.util.find_spec('shapely').origin).parent)"
Copy-Item -LiteralPath (Join-Path $geosPrefix 'bin\geos.dll') -Destination $shapelyFolder
Copy-Item -LiteralPath (Join-Path $geosPrefix 'bin\geos_c.dll') -Destination $shapelyFolder
}
if ($Stage -eq 'opencv') {
$env:CMAKE_ARGS = '-DBUILD_LIST=core,imgproc,imgcodecs,python3 -DWITH_FFMPEG=OFF -DWITH_MSMF=OFF -DWITH_DSHOW=OFF -DWITH_OPENCL=OFF -DBUILD_TESTS=OFF -DBUILD_PERF_TESTS=OFF -DCMAKE_CXX_FLAGS=/MP'
$env:CMAKE_BUILD_PARALLEL_LEVEL = '4'
$env:CMAKE_GENERATOR = 'Visual Studio 18 2026'
python -m pip install --no-build-isolation --no-binary=opencv-python opencv-python
if ($LASTEXITCODE) { throw 'Falha ao compilar OpenCV' }
}
