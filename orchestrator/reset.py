import subprocess

print("🔥 Iniciando reset do ambiente...")

# padrões de clientes (ajuste se quiser)
patterns = ["cliente", "loja", "rodrigo", "claude"]

# pegar containers
result = subprocess.run(
    ["docker", "ps", "-a", "--format", "{{.Names}}"],
    capture_output=True,
    text=True
)

containers = result.stdout.splitlines()

# filtrar clientes
to_remove = [c for c in containers if any(p in c for p in patterns)]

print(f"🧾 Containers encontrados: {to_remove}")

# parar containers
for c in to_remove:
    subprocess.run(["docker", "stop", c])

# remover containers
for c in to_remove:
    subprocess.run(["docker", "rm", c])

print("🧹 Containers removidos")

# remover volumes
volumes = subprocess.run(
    ["docker", "volume", "ls", "--format", "{{.Name}}"],
    capture_output=True,
    text=True
).stdout.splitlines()

vol_to_remove = [v for v in volumes if any(p in v for p in patterns)]

print(f"💾 Volumes encontrados: {vol_to_remove}")

for v in vol_to_remove:
    subprocess.run(["docker", "volume", "rm", v])

print("✅ Reset finalizado!")
