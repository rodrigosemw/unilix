from flask import Flask, request, jsonify
import threading
from flask_cors import CORS
import subprocess, os, secrets, hmac, hashlib, base64, json, shutil, re, urllib.request
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
CORS(app)

CLIENTES_DIR   = os.environ.get('CLIENTES_DIR', '/clientes')
DOMAIN         = os.environ.get('DOMAIN', 'unilix.tech')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', 'changeme')
MASTER_URL     = os.environ.get('MASTER_URL', '')
MASTER_KEY     = os.environ.get('MASTER_KEY', '')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
EMAIL_FROM     = os.environ.get('EMAIL_FROM', 'noreply@unilix.tech')

# Jobs assíncronos via arquivo compartilhado
import tempfile
_JOBS_DIR = '/tmp/orch_jobs'
os.makedirs(_JOBS_DIR, exist_ok=True)

def _job_set(job_id, data):
    with open(f'{_JOBS_DIR}/{job_id}.json', 'w') as f:
        json.dump(data, f)

def _job_get(job_id):
    try:
        with open(f'{_JOBS_DIR}/{job_id}.json') as f:
            return json.load(f)
    except:
        return None

from datetime import datetime as _dt_cls

def _slug_exists_master(slug):
    """Verifica se slug já existe no Supabase master."""
    if not MASTER_URL or not MASTER_KEY:
        return False
    try:
        req = urllib.request.Request(
            f'{MASTER_URL}/rest/v1/clientes?subdominio=eq.{slug}&select=id',
            headers={
                'apikey': MASTER_KEY,
                'Authorization': f'Bearer {MASTER_KEY}',
            }
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            return len(json.loads(r.read())) > 0
    except:
        return False



def gerar_jwt(secret, role='anon'):
    def b64url(data):
        if isinstance(data, str): data = data.encode()
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode()
    header  = b64url(json.dumps({'alg':'HS256','typ':'JWT'}, separators=(',',':')))
    payload = b64url(json.dumps({'role': role}, separators=(',',':')))
    msg = f'{header}.{payload}'
    sig = b64url(hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest())
    return f'{msg}.{sig}'

def gerar_hash(senha):
    import bcrypt
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt(10)).decode()

def enviar_email_boas_vindas(nome, email, url, login, senha):
    if not RESEND_API_KEY:
        print('[EMAIL] RESEND_API_KEY não configurada — email não enviado')
        return

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"/></head>
<body style="margin:0;padding:0;background:#F5F7FF;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F7FF;padding:40px 0;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(91,94,244,0.10);">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#5B5EF4,#00D2FF);padding:36px 40px;text-align:center;">
            <h1 style="margin:0;color:#fff;font-size:1.75rem;font-weight:800;letter-spacing:-0.02em;">🛒 ListaFácil</h1>
            <p style="margin:8px 0 0;color:rgba(255,255,255,0.85);font-size:0.95rem;">by Unilix</p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px 40px 32px;">
            <h2 style="margin:0 0 8px;color:#111827;font-size:1.25rem;font-weight:700;">Olá, {nome}! 🎉</h2>
            <p style="margin:0 0 24px;color:#6B7280;line-height:1.7;">
              Sua conta no <strong>ListaFácil</strong> foi criada com sucesso. Agora você pode controlar listas de compras e estoque do seu restaurante de qualquer lugar.
            </p>

            <!-- Credenciais -->
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#F5F7FF;border-radius:12px;margin-bottom:28px;">
              <tr>
                <td style="padding:24px 28px;">
                  <p style="margin:0 0 16px;color:#111827;font-weight:700;font-size:0.9375rem;">📋 Seus dados de acesso:</p>
                  <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding:6px 0;color:#6B7280;font-size:0.875rem;width:100px;">🔗 Endereço</td>
                      <td style="padding:6px 0;"><a href="{url}" style="color:#5B5EF4;font-weight:600;text-decoration:none;">{url}</a></td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0;color:#6B7280;font-size:0.875rem;">👤 Login</td>
                      <td style="padding:6px 0;color:#111827;font-weight:600;">{login}</td>
                    </tr>
                    <tr>
                      <td style="padding:6px 0;color:#6B7280;font-size:0.875rem;">🔑 Senha</td>
                      <td style="padding:6px 0;">
                        <code style="background:#E5E7EB;padding:3px 10px;border-radius:6px;font-size:0.9rem;color:#111827;font-weight:700;">{senha}</code>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>

            <!-- CTA -->
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td align="center">
                  <a href="{url}" style="display:inline-block;background:linear-gradient(135deg,#5B5EF4,#00D2FF);color:#fff;text-decoration:none;padding:14px 36px;border-radius:10px;font-weight:700;font-size:0.9375rem;">
                    Acessar o ListaFácil →
                  </a>
                </td>
              </tr>
            </table>

            <p style="margin:28px 0 0;color:#6B7280;font-size:0.8125rem;line-height:1.6;">
              Guarde sua senha em local seguro. Se precisar de ajuda, responda este email.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:20px 40px;border-top:1px solid #E5E7EB;text-align:center;">
            <p style="margin:0;color:#9CA3AF;font-size:0.8rem;">© 2026 Unilix. Feito com 💜 no Brasil.</p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""

    payload = json.dumps({
        'from': f'ListaFácil <{EMAIL_FROM}>',
        'to': [email],
        'subject': f'🛒 Sua conta no ListaFácil está pronta, {nome}!',
        'html': html
    }).encode()

    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=payload,
        headers={
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    try:
        resultado = subprocess.run(
            ['python3', '/host/send_email.py', json.dumps({
                'email': email,
                'subject': f'🛒 Sua conta no ListaFácil está pronta, {nome}!',
                'html': html
            })],
            capture_output=True, text=True
        )
        print(f'[EMAIL] {resultado.stdout} {resultado.stderr}')
    except Exception as e:
        print(f'[EMAIL] Erro ao enviar para {email}: {e}')

def registrar_master(cliente_id, nome, email, plano, subdominio, container_name):
    if not MASTER_URL or not MASTER_KEY:
        return
    try:
        payload = json.dumps({
            'nome': nome, 'email': email, 'plano_id': plano,
            'status': 'ativo', 'subdominio': subdominio
        }).encode()
        req = urllib.request.Request(
            f'{MASTER_URL}/rest/v1/clientes',
            data=payload,
            headers={
                'apikey': MASTER_KEY,
                'Authorization': f'Bearer {MASTER_KEY}',
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }, method='POST'
        )
        with urllib.request.urlopen(req) as r:
            cliente = json.loads(r.read())[0]

        payload2 = json.dumps({
            'cliente_id': cliente['id'],
            'container_name': container_name,
            'status': 'ativo',
            'supabase_url': f'https://{subdominio}.{DOMAIN}'
        }).encode()
        req2 = urllib.request.Request(
            f'{MASTER_URL}/rest/v1/containers',
            data=payload2,
            headers={
                'apikey': MASTER_KEY,
                'Authorization': f'Bearer {MASTER_KEY}',
                'Content-Type': 'application/json'
            }, method='POST'
        )
        urllib.request.urlopen(req2)
    except Exception as e:
        print(f'[MASTER] Erro ao registrar: {e}')

def criar_cliente(nome, email, plano='starter', subdominio_escolhido=None, senha_cliente=None, modulos=None):
    if modulos is None:
        modulos = ['estoque']

    if subdominio_escolhido:
        slug = re.sub(r'[^a-z0-9]', '', subdominio_escolhido.lower())[:30]
        if os.path.exists(f'{CLIENTES_DIR}/{slug}') or _slug_exists_master(slug):
            return {'ok': False, 'erro': 'Subdomínio já está em uso'}
    else:
        # Usa o nome em vez do email para gerar slug mais legível
        base_slug = re.sub(r'[^a-z0-9]', '', nome.strip().lower().replace(' ', ''))[:20]
        if not base_slug or len(base_slug) < 3:
            base_slug = re.sub(r'[^a-z0-9]', '', email.split('@')[0].lower())[:20]
        slug = base_slug
        attempt = 0
        while os.path.exists(f'{CLIENTES_DIR}/{slug}') or _slug_exists_master(slug):
            attempt += 1
            slug = base_slug[:16] + secrets.token_hex(2)
            if attempt > 10:
                slug = secrets.token_hex(8)
                break

    db_pass     = secrets.token_urlsafe(20)
    jwt_secret  = secrets.token_urlsafe(32)
    admin_senha = senha_cliente if senha_cliente else secrets.token_urlsafe(10)
    admin_login = re.sub(r'[^a-z0-9]', '', nome.strip().split()[0].lower())[:20] or 'admin'
    admin_hash  = admin_senha  # Hub compara texto puro; ListaFácil faz hash no 1º login
    anon_jwt    = gerar_jwt(jwt_secret)
    pasta       = f'{CLIENTES_DIR}/{slug}'
    BASE_DIR = Path(__file__).resolve().parent
    tpl = str(BASE_DIR / 'templates')
    os.makedirs(pasta, exist_ok=True)

    # Copia arquivos base
    for f in ['entrypoint.sh', 'hub.html', 'lista-compras-saas.html']:
        src = f'{tpl}/{f}'
        if os.path.exists(src):
            shutil.copy(src, pasta)
        else:
            print(f'[AVISO] Template não encontrado: {f}')

    # Gera Dockerfile dinamicamente baseado nos módulos
    dockerfile_lines = [
        'FROM nginx:alpine',
        'COPY hub.html /tmp/hub.html',
        'COPY lista-compras-saas.html /tmp/listafacil.html',
    ]
    # Módulo estoque — ContagemFácil
    if 'estoque' in modulos and os.path.exists(f'{tpl}/contagem.html'):
        shutil.copy(f'{tpl}/contagem.html', pasta)
        dockerfile_lines.append('COPY contagem.html /tmp/contagem.html')
    # Módulo PDV
pdv_tpl = str(Path(tpl) / 'pdv')
    if 'pdv' in modulos and os.path.exists(f'{pdv_tpl}/comanda-facil.html'):
        shutil.copy(f'{pdv_tpl}/comanda-facil.html', f'{pasta}/comanda-facil.html')
        dockerfile_lines.append('COPY comanda-facil.html /tmp/comandafacil.html')
    dockerfile_lines += [
        'COPY nginx.conf /etc/nginx/conf.d/default.conf',
        'COPY entrypoint.sh /entrypoint.sh',
        'RUN chmod +x /entrypoint.sh',
        'ENTRYPOINT ["/entrypoint.sh"]',
    ]
    with open(f'{pasta}/Dockerfile', 'w') as fh:
        fh.write('\n'.join(dockerfile_lines) + '\n')

    # nginx com nome completo do container postgrest
    nginx_lines = [
        'server {',
        '    listen 80;',
        '    root /usr/share/nginx/html;',
        '    index index.html;',
        '    location / { try_files $uri $uri/ /index.html; }',
        '    location /estoque/ { try_files $uri $uri/ /estoque/listafacil.html; }',
        '    location /estoque/contagem.html { try_files $uri =404; }',
        '    location /pdv/ { try_files $uri $uri/ /pdv/comandafacil.html; }',
        '    location /rest/v1/ {',
        '        resolver 127.0.0.11 valid=30s;',
        f'        set $upstream {slug}-postgrest;',
        '        rewrite ^/rest/v1/(.*)$ /$1 break;',
        '        proxy_pass http://$upstream:3000;',
        '        proxy_set_header Host $host;',
        '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;',
        '        proxy_set_header apikey $http_apikey;',
        '        proxy_set_header Authorization $http_authorization;',
        '        proxy_set_header Accept "application/json";',
        '    }',
        '}',
    ]
    with open(f'{pasta}/nginx.conf', 'w') as fh:
        fh.write('\n'.join(nginx_lines) + '\n')

    # schema unificado
    modulos_sql = '{' + ','.join(modulos) + '}'
    schema = open(f'{tpl}/schema.sql').read()
    schema = (schema
        .replace('{{NOME}}',        nome)
        .replace('{{PLANO}}',       plano)
        .replace('{{ADMIN_HASH}}',  admin_hash)
        .replace('{{ADMIN_LOGIN}}', admin_login)
        .replace('{{DB_PASS}}',     db_pass)
        .replace('{{MODULOS}}',     modulos_sql))
    with open(f'{pasta}/schema.sql', 'w') as fh:
        fh.write(schema)

    compose = f"""services:
  nginx:
    build: .
    container_name: {slug}
    restart: always
    depends_on:
      - postgrest
    environment:
      - SUPABASE_URL=https://{slug}.{DOMAIN}
      - SUPABASE_KEY={anon_jwt}
      - CLIENTE_ID={slug}
      - PLANO={plano}
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=traefik_proxy"
      - "traefik.http.routers.{slug}.rule=Host(`{slug}.{DOMAIN}`)"
      - "traefik.http.routers.{slug}.entrypoints=websecure"
      - "traefik.http.routers.{slug}.tls.certresolver=letsencrypt"
      - "traefik.http.services.{slug}.loadbalancer.server.port=80"
    networks:
      - traefik_proxy
      - {slug}_internal
  postgres:
    image: postgres:16-alpine
    container_name: {slug}-postgres
    restart: always
    environment:
      - POSTGRES_DB={slug}
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD={db_pass}
    volumes:
      - ./pgdata:/var/lib/postgresql/data
      - ./schema.sql:/docker-entrypoint-initdb.d/01-schema.sql
    networks:
      - {slug}_internal
  postgrest:
    image: postgrest/postgrest
    container_name: {slug}-postgrest
    restart: always
    environment:
      - PGRST_DB_URI=postgres://authenticator:{db_pass}@postgres:5432/{slug}
      - PGRST_DB_SCHEMA=public
      - PGRST_DB_ANON_ROLE=anon
      - PGRST_JWT_SECRET={jwt_secret}
    depends_on:
      - postgres
    networks:
      - {slug}_internal
networks:
  traefik_proxy:
    external: true
  {slug}_internal:
    name: {slug}_internal
    driver: bridge
"""
    with open(f'{pasta}/docker-compose.yml', 'w') as fh:
        fh.write(compose)

    resultado = subprocess.run(
        ['docker', 'compose', 'up', '-d', '--build'],
        cwd=pasta, capture_output=True, text=True
    )
    # Aguarda containers iniciarem
    import time
    time.sleep(8)

    url = f'https://{slug}.{DOMAIN}'
    # Log seguro de criação (senha em texto para recuperação)
    log_entry = {
        'ts': datetime.now().isoformat(),
        'slug': slug, 'nome': nome, 'email': email,
        'plano': plano, 'url': url, 'admin_login': admin_login, 'admin_senha': admin_senha
    }
    log_path = '/home/ubuntu/clientes/.criacao_log.json'
    try:
        logs = []
        if os.path.exists(log_path):
            with open(log_path) as lf:
                logs = json.load(lf)
        logs.append(log_entry)
        with open(log_path, 'w') as lf:
            json.dump(logs, lf, indent=2, ensure_ascii=False)
        os.chmod(log_path, 0o600)  # só root/ubuntu lê
    except Exception as e:
        print(f'[LOG] Erro ao salvar log: {e}')
    registrar_master(slug, nome, email, plano, slug, slug)

    # Envia email de boas-vindas com credenciais
    enviar_email_boas_vindas(nome, email, url, admin_login, admin_senha)

    return {
        'ok': True, 'cliente_id': slug,
        'url': url,
        'login': admin_login, 'senha': admin_senha, 'plano': plano
    }

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'ok': True})

@app.route('/enviar-email', methods=['POST'])
def enviar_email_endpoint():
    data = request.json or {}
    to_email = data.get('to_email', '')
    to_name  = data.get('to_name', '')
    subject  = data.get('subject', '')
    html     = data.get('html', '')
    if not to_email or not subject or not html:
        return jsonify({'erro': 'to_email, subject e html obrigatorios'}), 400
    resultado = subprocess.run(
        ['python3', '/host/send_email.py', json.dumps({
            'email': to_email,
            'subject': subject,
            'html': html
        })],
        capture_output=True, text=True
    )
    ok = 'OK' in resultado.stdout
    return jsonify({'ok': ok, 'log': resultado.stdout + resultado.stderr})

@app.route('/buscar-cliente', methods=['POST'])
def buscar_cliente():
    data = request.json or {}
    email = data.get('email', '')
    if not email:
        return jsonify({'erro': 'email obrigatorio'}), 400
    slug = re.sub(r'[^a-z0-9]', '', email.lower())[:20]
    pasta = f'{CLIENTES_DIR}/{slug}'
    if os.path.exists(pasta):
        return jsonify({'ok': True, 'url': f'https://{slug}.{DOMAIN}', 'cliente_id': slug})
    return jsonify({'ok': False})

@app.route('/criar-cliente', methods=['POST'])
def criar_manual():
    data = request.json or {}
    if not data.get('nome') or not data.get('email'):
        return jsonify({'erro': 'nome e email obrigatórios'}), 400
    email = data['email']
    # Verifica email duplicado no log
    log_path = '/home/ubuntu/clientes/.criacao_log.json'
    try:
        with open(log_path) as lf:
            logs = json.load(lf)
        for entry in logs:
            if entry.get('email', '').lower() == email.lower():
                return jsonify({'ok': False, 'erro': 'Este e-mail já possui uma conta. Acesse pelo link que enviamos.', 'url': f"https://{entry['slug']}.{DOMAIN}"})
    except:
        pass
    slug = re.sub(r'[^a-z0-9]', '', email.lower())[:20]
    if os.path.exists(f'{CLIENTES_DIR}/{slug}'):
        return jsonify({'ok': False, 'erro': 'Este e-mail já possui uma conta.'})
    # Cria job assíncrono
    job_id = secrets.token_hex(8)
    _job_set(job_id, {'status': 'pending', 'result': None})
    def run():
        result = criar_cliente(data['nome'], email, data.get('plano','starter'), data.get('subdominio'), data.get('senha'), data.get('modulos',['estoque']))
        _job_set(job_id, {'status': 'done' if result.get('ok') else 'error', 'result': result})
    threading.Thread(target=run, daemon=True).start()
    return jsonify({'ok': True, 'job_id': job_id, 'status': 'pending'})

@app.route('/status/<job_id>', methods=['GET'])
def job_status(job_id):
    job = _job_get(job_id)
    if not job:
        return jsonify({'status': 'not_found'}), 404
    return jsonify({'status': job['status'], 'result': job['result']})



def criar_cliente_pdv(nome, email, plano='starter', subdominio_escolhido=None, senha_cliente=None):
    """Provisiona um container ComandaFácil para o cliente."""
    if subdominio_escolhido:
        slug = re.sub(r'[^a-z0-9]', '', subdominio_escolhido.lower())[:30] + '-pdv'
        if os.path.exists(f'{CLIENTES_DIR}/{slug}') or _slug_exists_master(slug):
            return {'ok': False, 'erro': 'Subdomínio PDV já está em uso'}
    else:
        base_slug = re.sub(r'[^a-z0-9]', '', email.lower())[:16] + '-pdv'
        slug = base_slug
        attempt = 0
        while os.path.exists(f'{CLIENTES_DIR}/{slug}') or _slug_exists_master(slug):
            attempt += 1
            slug = base_slug[:12] + '-pdv-' + secrets.token_hex(2)
            if attempt > 10:
                slug = secrets.token_hex(6) + '-pdv'
                break

    db_pass    = secrets.token_urlsafe(20)
    jwt_secret = secrets.token_urlsafe(32)
    admin_senha = senha_cliente if senha_cliente else secrets.token_urlsafe(10)
    admin_login = re.sub(r'[^a-z0-9]', '', nome.strip().split()[0].lower())[:20] or 'admin'
    admin_hash  = gerar_hash(admin_senha)
    anon_jwt    = gerar_jwt(jwt_secret)
    pasta       = f'{CLIENTES_DIR}/{slug}'
    os.makedirs(pasta, exist_ok=True

    for f in ['Dockerfile', 'entrypoint.sh', 'comanda-facil.html']:
        shutil.copy(f'{pdv_tpl}/{f}', pasta)

    # nginx — gera com nome correto do container postgrest
    nginx_content = open(f'{pdv_tpl}/nginx.conf').read()
    nginx_content = nginx_content.replace('pdvteste-pdv-postgrest', f'{slug}-postgrest')
    open(f'{pasta}/nginx.conf', 'w').write(nginx_content)

    # schema com hash do admin
    schema = open(f'{pdv_tpl}/schema-pdv.sql').read()
    schema = schema.replace('__ADMIN_HASH__', admin_senha)
    schema = schema.replace('__DB_PASS__', db_pass)
    open(f'{pasta}/schema-pdv.sql', 'w').write(schema)

    url = f'https://{slug}.{DOMAIN}'

    compose = f"""services:
  nginx:
    build: .
    container_name: {slug}
    restart: always
    depends_on:
      - postgrest
    environment:
      - SUPABASE_URL=https://{slug}.{DOMAIN}
      - SUPABASE_KEY={anon_jwt}
      - CLIENTE_ID={slug}
      - PLANO={plano}
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=traefik_proxy"
      - "traefik.http.routers.{slug}.rule=Host(`{slug}.{DOMAIN}`)"
      - "traefik.http.routers.{slug}.entrypoints=websecure"
      - "traefik.http.routers.{slug}.tls.certresolver=letsencrypt"
      - "traefik.http.services.{slug}.loadbalancer.server.port=80"
    networks:
      - traefik_proxy
      - {slug}_internal
  postgres:
    image: postgres:16-alpine
    container_name: {slug}-postgres
    restart: always
    environment:
      - POSTGRES_DB={slug}
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD={db_pass}
    volumes:
      - ./pgdata:/var/lib/postgresql/data
      - ./schema-pdv.sql:/docker-entrypoint-initdb.d/01-schema.sql
    networks:
      - {slug}_internal
  postgrest:
    image: postgrest/postgrest
    container_name: {slug}-postgrest
    restart: always
    environment:
      - PGRST_DB_URI=postgres://authenticator:{db_pass}@postgres:5432/{slug}
      - PGRST_DB_SCHEMA=public
      - PGRST_DB_ANON_ROLE=anon
      - PGRST_JWT_SECRET={jwt_secret}
      - PGRST_DB_POOL=5
    depends_on:
      - postgres
    networks:
      - {slug}_internal
networks:
  traefik_proxy:
    external: true
  {slug}_internal:
    name: {slug}_internal
    driver: bridge
"""
    open(f'{pasta}/docker-compose.yml', 'w').write(compose)

    resultado = subprocess.run(
        ['docker', 'compose', 'up', '-d', '--build'],
        cwd=pasta, capture_output=True, text=True
    )
    # Aguarda containers iniciarem
    import time
    time.sleep(8)
    if resultado.returncode != 0:
        return {'ok': False, 'erro': resultado.stderr[-500:]}

    registrar_master(slug, nome, email, f'pdv-{plano}', slug, slug)
    enviar_email_boas_vindas(nome, email, url, admin_login, admin_senha)

    return {
        'ok': True,
        'cliente_id': slug,
        'url': url,
        'login': admin_login,
        'senha': admin_senha,
        'plano': plano
    }


@app.route('/criar-cliente-pdv', methods=['POST'])
def criar_cliente_pdv_route():
    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    if not email:
        return jsonify({'ok': False, 'erro': 'email obrigatorio'}), 400
    nome = data.get('nome', email)
    return jsonify(criar_cliente_pdv(nome, email, data.get('plano','starter'), data.get('subdominio'), data.get('senha')))

@app.route('/webhook/kiwify', methods=['POST'])
def webhook_kiwify():
    # Log completo para debug
    print(f'[KIWIFY DEBUG] Headers: {dict(request.headers)}')
    print(f'[KIWIFY DEBUG] Args: {dict(request.args)}')
    print(f'[KIWIFY DEBUG] Body: {request.get_data(as_text=True)[:500]}')
    # Log tudo para debug
    print(f'[KIWIFY DEBUG] Headers: {dict(request.headers)}')
    print(f'[KIWIFY DEBUG] Body: {request.get_data(as_text=True)[:300]}')
    data = request.json or {}
    event = data.get('event', '')
    print(f'[KIWIFY] Evento recebido: {event} | Data: {str(data)[:200]}')

    # Eventos que disparam criação de cliente (inglês e português)
    eventos_criar = (
        'order_approved', 'subscription_activated', 'subscription_renewed',
        'order.approved', 'subscription.activated',
        'compra_aprovada', 'assinatura_ativada', 'assinatura_renovada'
    )

    if event not in eventos_criar:
        return jsonify({'ok': True, 'msg': f'evento ignorado: {event}'})

    customer = data.get('Customer', data.get('customer', {}))
    email    = customer.get('email', '')
    nome     = customer.get('full_name', customer.get('name', email))
    produto  = data.get('Product', data.get('product', {})).get('name', '').lower()

    if 'gold' in produto:
        plano = 'gold'
    elif 'pro' in produto:
        plano = 'pro'
    else:
        plano = 'starter'

    if not email:
        return jsonify({'ok': False, 'erro': 'email ausente'}), 400

    print(f'[KIWIFY] Criando cliente: {email} plano={plano}')

    customer = data.get('Customer', {})
    email    = customer.get('email', '')
    nome     = customer.get('full_name', email)
    produto  = data.get('Product', {}).get('name', '').lower()
    oferta   = data.get('Subscription', {}).get('plan', {}).get('name', '').lower() if 'Subscription' in data else ''

    # Detecta plano pelo nome do produto
    if 'gold' in produto:
        plano = 'gold'
    elif 'pro' in produto:
        plano = 'pro'
    else:
        plano = 'starter'

    if not email:
        return jsonify({'ok': False, 'erro': 'email ausente'}), 400

    print(f'[KIWIFY] Evento={event} email={email} plano={plano}')
    resultado = criar_cliente(nome, email, plano)
    return jsonify(resultado)

@app.route('/webhook/lemonsqueezy', methods=['POST'])
def webhook_lemon():
    sig      = request.headers.get('X-Signature', '')
    body     = request.get_data()
    expected = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return jsonify({'erro': 'assinatura inválida'}), 401
    data  = request.json
    event = data.get('meta', {}).get('event_name', '')
    if event in ('order_created', 'subscription_created'):
        attrs   = data['data']['attributes']
        email   = attrs.get('user_email', '')
        nome    = attrs.get('user_name', email)
        variant = attrs.get('variant_name', '').lower()
        plano   = 'gold' if 'gold' in variant else 'pro' if 'pro' in variant else 'starter'
        print(f'[WEBHOOK] Criando cliente: {email} plano={plano}')
        criar_cliente(nome, email, plano)
    return jsonify({'ok': True})


@app.route('/verificar-subdominio', methods=['POST'])
def verificar_subdominio():
    data = request.json or {}
    slug = re.sub(r'[^a-z0-9]', '', data.get('subdominio', '').lower())[:30]
    if not slug or len(slug) < 3:
        return jsonify({'disponivel': False, 'erro': 'Mínimo 3 caracteres'})
    existe = os.path.exists(f'{CLIENTES_DIR}/{slug}') or _slug_exists_master(slug)
    return jsonify({'disponivel': not existe, 'slug': slug})


@app.route('/verificar-email', methods=['POST'])
def verificar_email():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    if not email:
        return jsonify({'disponivel': False, 'erro': 'Email obrigatório'})
    slug = re.sub(r'[^a-z0-9]', '', email)[:20]
    # Verifica pela pasta do cliente
    for pasta in os.listdir(CLIENTES_DIR):
        log_path = '/home/ubuntu/clientes/.criacao_log.json'
        try:
            import json as _json
            with open(log_path) as lf:
                logs = _json.load(lf)
            for entry in logs:
                if entry.get('email', '').lower() == email:
                    return jsonify({'disponivel': False})
        except:
            pass
    return jsonify({'disponivel': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
