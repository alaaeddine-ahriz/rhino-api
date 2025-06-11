#!/usr/bin/env python3
"""
Script pour démarrer le monitoring automatique des emails en arrière-plan
"""

import subprocess
import sys
import os

def start_monitoring_background():
    """Démarre le monitoring en arrière-plan"""
    try:
        # Obtenir le chemin du script de monitoring
        script_path = os.path.join(os.path.dirname(__file__), 'monitor_replies.py')
        
        # Démarrer le processus en arrière-plan
        process = subprocess.Popen([
            sys.executable, script_path, 
            '--interval', '30'  # Vérifier toutes les 30 secondes
        ], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT,
        universal_newlines=True
        )
        
        print(f"🚀 Monitoring automatique démarré en arrière-plan (PID: {process.pid})")
        print("📧 Le système va automatiquement:")
        print("   - Lire les nouvelles réponses email")
        print("   - Évaluer automatiquement les réponses")
        print("   - Envoyer les feedbacks dans le même thread email")
        print("   - Vérifier toutes les 30 secondes")
        print("")
        print("🛑 Pour arrêter le monitoring:")
        print(f"   kill {process.pid}")
        print("   ou Ctrl+C si vous restez dans ce terminal")
        
        # Afficher les logs en temps réel
        try:
            for line in process.stdout:
                print(line.strip())
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du monitoring demandé par l'utilisateur")
            process.terminate()
            process.wait()
            print("✅ Monitoring arrêté")
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du monitoring: {e}")
        return False
    
    return True

def start_monitoring_foreground():
    """Démarre le monitoring en premier plan (pour debug)"""
    import monitor_replies
    print("🐛 Mode debug: monitoring en premier plan")
    monitor_replies.monitor_emails(check_interval=15)  # Vérifier toutes les 15 secondes en debug

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Démarrer le monitoring automatique des emails")
    parser.add_argument("--debug", "-d", action="store_true", 
                       help="Mode debug: monitoring en premier plan avec logs détaillés")
    
    args = parser.parse_args()
    
    if args.debug:
        start_monitoring_foreground()
    else:
        start_monitoring_background() 