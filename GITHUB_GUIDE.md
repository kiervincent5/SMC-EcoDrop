# 🚀 EcoDrop: GitHub Upload & Git Guide

This guide will help you upload your project to GitHub and teach you the basics of version control.

---

## 1. Core Concepts (The "Why")

*   **Git**: A tool on your computer that saves "snapshots" of your code. Think of it like game save points.
*   **GitHub**: A website that hosts your Git "save points" in the cloud. It allows you to share your code and collaborate.
*   **Repository (Repo)**: A project folder tracked by Git.
*   **Commit**: A "save point" with a message explaining what you changed.
*   **Push**: Uploading your local commits to GitHub.

---

## 2. Step-by-Step: Your First Upload

### Step A: Prepare your GitHub Account
1.  Go to [github.com](https://github.com/) and sign in.
2.  Click the **+** icon in the top right and select **New repository**.
3.  Name it `ecodrop-main`.
4.  Keep it **Public** (or Private if you prefer).
5.  **Critically**: Do NOT initialize with a README, .gitignore, or license (since you already have them).
6.  Click **Create repository**.

### Step B: Run these commands in your terminal
Open your terminal in this folder (`c:\Users\acer\Desktop\ecodrop-main`) and run:

```powershell
# 1. Initialize Git in this folder
git init

# 2. Add all files to the "staging area"
# (Notice how it ignores files in your .gitignore automatically!)
git add .

# 3. Create your first "save point"
git commit -m "Initial commit of EcoDrop project"

# 4. Set the main branch name
git branch -M main

# 5. Connect your local folder to GitHub 
git remote add origin https://github.com/kiervincent5/SMC-EcoDrop.git

# 6. Push your code to GitHub
git push -u origin main
```

---

## 3. Daily Workflow (The "How")

Once you are set up, this is what you will do every time you make changes:

1.  **Modify** your files.
2.  **Stage** changes: `git add .`
3.  **Commit** changes: `git commit -m "Describe what you did"`
4.  **Push** to cloud: `git push`

---

## 4. Why `.gitignore` matters?

Your project has a `.gitignore` file. This tells Git **not** to upload:
- `db.sqlite3`: Your local database (which might have private test data).
- `.env`: Your secret keys and passwords.
- `venv/`: Your large virtual environment folder.

---

## 5. Cheat Sheet

| Command | Action |
| :--- | :--- |
| `git status` | See what files have changed. |
| `git log --oneline` | See your history of "save points". |
| `git pull` | Download latest changes from GitHub (if you worked elsewhere). |

> [!TIP]
> **Learning Tip**: Whenever you are about to do a big change, make a commit first. If you mess up, you can always go back to that "save point"!
