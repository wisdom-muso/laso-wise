# 🚀 One-Command VPS Setup

## Quick Deployment on Your VPS (65.108.91.110)

SSH into your VPS and run this single command:

```bash
curl -fsSL https://gitlab.com/wisdomlasome-group/laso-wise/-/raw/master/quick-setup.sh | bash
```

**Alternative (if you prefer to review the script first):**

```bash
# Download and review the setup script
wget https://gitlab.com/wisdomlasome-group/laso-wise/-/raw/master/quick-setup.sh
cat quick-setup.sh  # Review the script
chmod +x quick-setup.sh
./quick-setup.sh
```

## What This Command Does:

1. ✅ **Updates system packages**
2. ✅ **Installs Docker and Docker Compose**
3. ✅ **Configures firewall (ports 22, 80, 443)**
4. ✅ **Clones the LASO Healthcare repository**
5. ✅ **Sets up production environment**
6. ✅ **Optionally runs the full deployment**

## After Setup:

Your LASO Healthcare Management System will be available at:

- **🌐 Main Site:** http://65.108.91.110/
- **🔐 Admin Panel:** http://65.108.91.110/admin/
  - Username: `admin`
  - Password: `8gJW48Tz8YXDrF57`

## Manual Deployment (if needed):

If you chose not to auto-deploy, you can run:

```bash
cd laso-wise
sudo ./deploy.sh
```

## System Features:

- 🏥 **Complete Healthcare Management System**
- 👥 **Patient Management**
- 📅 **Appointment Scheduling**
- 💻 **Telemedicine Platform**
- 📋 **Medical Records & Imaging**
- 📊 **Analytics & Reporting**
- 🔒 **Secure Authentication**
- ⚡ **High Performance with PostgreSQL & Redis**

## Support:

For issues or questions, check the full deployment guide: `VPS_DEPLOYMENT_GUIDE.md`

---

**That's it! One command to deploy your entire healthcare management system! 🎉**