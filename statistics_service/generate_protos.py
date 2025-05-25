import subprocess
import os
import sys


def fix_imports(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    content = content.replace('import statistics_pb2 as statistics__pb2',
                              'from statistics_service.generated import statistics_pb2 as statistics__pb2')

    with open(file_path, 'w') as f:
        f.write(content)


def generate_protos():
    proto_dir = "/app/protos"
    output_dir = "/app/statistics_service/generated"

    os.makedirs(output_dir, exist_ok=True)

    proto_file = os.path.join(proto_dir, "statistics.proto")

    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"-I{proto_dir}",
        f"--python_out={output_dir}",
        f"--grpc_python_out={output_dir}",
        proto_file
    ]

    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error generating protos: {result.stderr}")
        sys.exit(1)

    # Create __init__.py
    init_file = os.path.join(output_dir, "__init__.py")
    with open(init_file, 'w') as f:
        f.write("# Generated proto files\n")

    # Fix imports
    grpc_file = os.path.join(output_dir, "statistics_pb2_grpc.py")
    if os.path.exists(grpc_file):
        fix_imports(grpc_file)


if __name__ == "__main__":
    generate_protos()