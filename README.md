# 🏥 OpenCareOS

> **The Open Source AI Operating Layer for Healthcare**
>
> Transform any existing Hospital Information System into an AI-native conversational platform powered by agentic AI.

<p align="center">
  <img alt="License" src="https://img.shields.io/badge/License-Apache%202.0-blue.svg">
  <img alt="Status" src="https://img.shields.io/badge/Status-Active%20Development-success">
  <img alt="Open Source" src="https://img.shields.io/badge/Open%20Source-Yes-brightgreen">
  <img alt="Built with NVIDIA" src="https://img.shields.io/badge/Powered%20by-NVIDIA%20Nemotron-76B900">
</p>

---

## 🚀 What is OpenCareOS?

OpenCareOS is an **open-source AI Operating Layer for Healthcare** that enables hospitals to become AI-native **without replacing their existing technology stack**.

Rather than building another Hospital Management System (HMS), OpenCareOS integrates with existing hospital software and allows patients, doctors, and administrators to interact with hospital services using natural language.

Imagine replacing dozens of menus, dashboards, and forms with a single intelligent conversational interface.

---

## 🎯 Vision

> **Every hospital should have an AI-native interface.**

Hospitals already have powerful systems for:

* Patient Management
* Electronic Medical Records (EMR/EHR)
* Billing
* Laboratory
* Pharmacy
* Scheduling
* Analytics

The problem isn't missing software.

The problem is that people still have to learn the software.

OpenCareOS changes that.

Users simply describe what they need, and OpenCareOS securely orchestrates the required workflows using AI agents.

---

# ✨ Key Features

* 🤖 Conversational AI Interface
* 🧠 Agentic AI Workflow Planning
* 🔒 Secure Tool Calling & Guardrails
* 🏥 Day-One Integration with Existing Hospital Systems
* 📁 File Upload & Document Understanding
* 📊 Multi-role Support
* 🔌 API-first Architecture
* 🏗️ Open Source & Extensible
* ☁️ Cloud or On-Prem Deployment
* ⚡ NVIDIA NIM & Local NIM Support

---

# 🏛 Architecture

```text
                    Patients
                    Doctors
                     Admins
                        │
                OpenCareOS Web UI
                        │
                Hermes Agent Platform
                        │
         Nemoclaw (Planning + Guardrails)
                        │
          NVIDIA Nemotron (NIM / Local NIM)
                        │
                Tool Calling Layer
                        │
      ┌──────────────┬──────────────┬──────────────┐
      │              │              │              │
Appointments     Reports       Billing      Inventory
      │              │              │              │
        Existing Hospital Backend APIs
                        │
                  Existing Database
```

---

# 💡 Example Workflows

## 👤 Patient

Instead of

* Login
* Navigate Appointments
* Search Doctors
* Pick Slot
* Confirm

The patient simply says:

> "Book me an appointment with a dermatologist tomorrow evening."

OpenCareOS:

* Understands intent
* Finds available doctors
* Books the appointment
* Returns confirmation

---

## 👨‍⚕️ Doctor

Doctor asks:

> "Summarize my patient's last five visits."

OpenCareOS:

* Retrieves patient history
* Summarizes previous consultations
* Highlights medications
* Displays lab trends

---

## 👨‍💼 Administrator

Administrator asks:

> "Show departments with the highest patient wait times."

OpenCareOS:

* Queries analytics
* Aggregates operational data
* Generates insights
* Suggests improvements

---

# 🛠 Technology Stack

## Frontend

* React
* TypeScript
* Tailwind CSS
* Modern Chat UI

## AI Agent Platform

* Hermes Agent Platform

## Agent Runtime

* Nemoclaw

## Language Model

* NVIDIA Nemotron
* NVIDIA NIM API
* Local NIM Deployment

## Backend

* REST APIs
* OpenAPI Tool Integration
* PostgreSQL / MySQL
* Existing Hospital Information Systems

---

# 🔒 Security

OpenCareOS is designed with enterprise-grade safety in mind.

Every AI action is executed through controlled tools.

Features include:

* Tool-level authorization
* Sandboxed execution
* Guardrails
* Role-based permissions
* Secure API orchestration

The AI never directly manipulates hospital databases.

All actions are routed through approved APIs.

---

# 🌍 Open Source Philosophy

OpenCareOS is built around one simple principle:

> Hospitals should not replace their software to adopt AI.

Instead, hospitals integrate OpenCareOS with their existing ecosystem.

Benefits include:

* Preserve existing investments
* Faster adoption
* Minimal migration effort
* Vendor independence
* Community-driven innovation

---

# 📜 License

Licensed under the **Apache License 2.0**.

You are free to use, modify, distribute, and build upon this project in accordance with the terms of the Apache 2.0 License.

---

# ❤️ Built for Healthcare. Powered by Open Source.

> **OpenCareOS is more than a chatbot.**
>
> It is an AI Operating Layer that enables every hospital to become conversational, intelligent, and future-ready without replacing its existing systems.
