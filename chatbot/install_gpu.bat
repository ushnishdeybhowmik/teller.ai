set CMAKE_ARGS=-DLLAMA_CUBLAS=on
pipenv install --skip-lock --skip-build llama-cpp-python --pre --upgrade --force-reinstall
