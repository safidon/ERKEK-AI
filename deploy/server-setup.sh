#!/usr/bin/env bash
# =====================================================
# ERKEK AI — жаңа Ubuntu 24.04 серверін дайындау
# =====================================================
# Бір рет, root ретінде іске қосылады:
#   bash deploy/server-setup.sh
#
# Не істейді:
#   1. Жүйені жаңартады, уақыт белдеуін Астана қылады
#   2. 2 GB swap қосады (2 GB RAM серверде build үшін керек)
#   3. Firewall: тек SSH, HTTP, HTTPS
#   4. Docker және Docker Compose орнатады (Ubuntu репозиторийінен)
#   5. Қауіпсіздік жаңартуларын автоматты қосады
#   6. SSH-қа тек кілтпен кіруге рұқсат етеді (құпиясөзбен — жоқ),
#      ЕГЕР root-та кемінде бір кілт орнатылған болса
#
# Скриптті қайта іске қосуға болады — бар нәрселерді бұзбайды.

set -euo pipefail

if [[ "$(id -u)" -ne 0 ]]; then
	echo "root ретінде іске қосыңыз." >&2
	exit 1
fi

export DEBIAN_FRONTEND=noninteractive

echo "==> 1/6 Жүйені жаңарту"
apt-get update -y
apt-get upgrade -y
apt-get install -y ca-certificates curl git ufw unattended-upgrades
timedatectl set-timezone Asia/Almaty || true

echo "==> 2/6 Swap (2 GB)"
if ! swapon --show | grep -q '/swapfile'; then
	fallocate -l 2G /swapfile
	chmod 600 /swapfile
	mkswap /swapfile
	swapon /swapfile
	grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
sysctl -w vm.swappiness=10 >/dev/null
grep -q '^vm.swappiness' /etc/sysctl.conf || echo 'vm.swappiness=10' >> /etc/sysctl.conf

echo "==> 3/6 Firewall"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw --force enable

echo "==> 4/6 Docker"
apt-get install -y docker.io docker-compose-v2
systemctl enable --now docker

echo "==> 5/6 Автоматты қауіпсіздік жаңартулары"
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "==> 6/6 SSH: тек кілтпен кіру"
if [[ -s /root/.ssh/authorized_keys ]]; then
	cat > /etc/ssh/sshd_config.d/99-erkekai.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
	sshd -t
	systemctl reload ssh || systemctl reload sshd
	echo "    Құпиясөзбен кіру өшірілді (кілт бар)."
else
	echo "    ЕСКЕРТУ: root-та SSH кілт жоқ — құпиясөзбен кіру қалдырылды." >&2
fi

echo
echo "Дайын:"
docker --version
docker compose version
free -h | sed -n '1,3p'
ufw status | head -n 8
