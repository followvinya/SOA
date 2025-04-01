import os
import subprocess
import sys


def generate_protos():
    # Проверяем наличие директории с proto-файлами
    proto_dir = "/app/protos"
    if not os.path.exists(proto_dir):
        print(f"Error: Proto directory {proto_dir} not found")
        return False

    # Проверяем наличие proto-файла
    proto_file = os.path.join(proto_dir, "posts.proto")
    if not os.path.exists(proto_file):
        print(f"Error: Proto file {proto_file} not found")
        return False

    # Создаем директорию для сгенерированных файлов, если она не существует
    generated_dir = "/app/generated"
    os.makedirs(generated_dir, exist_ok=True)

    # Генерируем Python файлы из proto
    try:
        result = subprocess.run([
            "python", "-m", "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={generated_dir}",
            f"--grpc_python_out={generated_dir}",
            proto_file
        ], check=True)

        if result.returncode == 0:
            print(f"Successfully generated proto files in {generated_dir}")
            # Выводим список сгенерированных файлов
            print(f"Generated files: {os.listdir(generated_dir)}")
            return True
        else:
            print(f"Error: protoc exited with code {result.returncode}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error executing protoc: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = generate_protos()
    sys.exit(0 if success else 1)