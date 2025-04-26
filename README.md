## 📚 g2w – Git Repository to Wordlist

g2w is a lightweight tool that crawls Git repositories (currently supports GitHub) and transforms the directory structure into a wordlist.

---
### ✨ Features
- Automatically crawls public GitHub repositories
- Detects branches and adjusts URL structure dynamically
- Creates a clean wordlist of file paths and directories
- Optional automatic URL-encoding for generated wordlists
- Color-coded, readable terminal output
- Verbose logging for better debugging and visibility

---

### ⚙️ Installation
```bash
git clone https://github.com/OffSecVik/git2wordlist
cd g2w
pip install -r requirements.txt
```

---

> **Note**:
> Required libraries: beautifulsoup4, requests, lxml

---

### 🚀 Usage
````bash
python g2w.py <repository_url> [options]
````
#### Example:
````bash
python g2w.py https://github.com/rapid7/metasploit-framework -v -o metasploit_wordlist.txt
````

---

### 📋 Options
| Option                 | Description                                                                         |
|------------------------|-------------------------------------------------------------------------------------|
| url	(Required)         | Target repository URL (currently supports GitHub only)                              |
| -o, --outfile          | Output file for the generated wordlist (if not provided, it will auto-generate one) |
| -v, --verbose          | 	Enable verbose logging                                                             |
| -a, --auto-url-encode	 | Automatically URL-encode paths in the output                                        |

---

### 💬 Example Output
```
app/
app/controllers/
app/models/
README.md
.gitignore
```

