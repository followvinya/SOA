import subprocess
import os
import sys


def fix_imports(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    content = content.replace('import posts_pb2 as posts__pb2',
                              'from post_service.generated import posts_pb2 as posts__pb2')

    with open(file_path, 'w') as f:
        f.write(content)


def generate_protos():
    proto_dir = "/app/protos"
    output_dir = "/app/post_service/generated"

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Generate Python code
    proto_file = os.path.join(proto_dir, "posts.proto")

    if not os.path.exists(proto_file):
        print(f"Error: Proto file not found at {proto_file}")
        sys.exit(1)

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
    else:
        print(f"Successfully generated proto files in {output_dir}")

    # Create __init__.py in generated directory
    init_file = os.path.join(output_dir, "__init__.py")
    with open(init_file, 'w') as f:
        f.write("# Generated proto files\n")

    # Fix imports in generated files
    grpc_file = os.path.join(output_dir, "posts_pb2_grpc.py")
    if os.path.exists(grpc_file):
        fix_imports(grpc_file)
        print("Fixed imports in posts_pb2_grpc.py")

    # List generated files
    generated_files = [f for f in os.listdir(output_dir) if f.endswith('.py')]
    print(f"Generated files: {generated_files}")


if __name__ == "__main__":
    generate_protos()