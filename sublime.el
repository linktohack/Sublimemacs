;; package & use-package
(setq package-archives '(("melpa" . "http://melpa.milkbox.net/packages/")       
                         ("gnu" . "http://elpa.gnu.org/packages/")))
(setq package-enable-at-startup nil)
(package-initialize)
(unless (package-installed-p 'use-package)
  (package-refresh-contents)
  (package-install 'use-package))
(require 'use-package)

;; server
(when (require 'server)
  (setq server-socket-dir "/tmp/sublime")
  (unless (server-running-p) (server-start)))

;; packages and configurations
(use-package org
  :mode ("\\.org\\'" . org-mode)
  :ensure t
  :pin gnu
  :init
  (setq org-confirm-babel-evaluate nil
        org-descriptive-links nil
        org-export-babel-evaluate 'inline-only
        org-latex-tables-booktabs t
        org-src-fontify-natively t
        org-src-preserve-indentation t)
  :config
  (org-babel-do-load-languages
   'org-babel-load-languages
   '((emacs-lisp . t)
     (ditaa . t)))
     (python . t)
     (ruby . t)
     (sh . t)
     (makefile . t)
  )