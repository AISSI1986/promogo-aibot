# Promogo Chat Vocal Widget

Un widget de chat vocal multilingue pour les sites web, supportant les langues haoussa, ewe, twi et ga.

## Fonctionnalités

- Interface intuitive et accessible
- Support multilingue (haoussa, ewe, twi, ga)
- Enregistrement audio en temps réel
- Intégration avec vos APIs STT, Rasa et TTS
- Design responsive et moderne
- Animations fluides et retours visuels

## Installation

### Option 1 : Installation rapide

1. Clonez le repository :
```bash
git clone [URL_DU_REPO]
cd promogo_bot
```

2. Installez les dépendances :
```bash
npm install
```

3. Configurez vos endpoints API dans `app.js` :
```javascript
this.apiEndpoints = {
    stt: 'VOTRE_API_STT',
    rasa: 'VOTRE_API_RASA',
    tts: 'VOTRE_API_TTS'
};
```

4. Démarrez le serveur de développement :
```bash
npm start
```

### Option 2 : Installation manuelle

1. Copiez les fichiers suivants dans votre projet :
   - `index.html`
   - `styles.css`
   - `app.js`
   - `assets/` (dossier contenant les icônes et images)

2. Configurez vos endpoints API dans `app.js`

3. Intégrez le widget dans votre page HTML :
```html
<link rel="stylesheet" href="styles.css">
<script src="app.js"></script>
```

## Structure du projet

```
promogo_bot/
├── index.html          # Structure HTML du widget
├── styles.css          # Styles CSS
├── app.js             # Logique JavaScript
├── package.json       # Configuration npm
├── README.md          # Documentation
├── .gitignore         # Configuration Git
└── assets/            # Ressources graphiques
    └── icons/         # Icônes SVG
```

## Personnalisation

### Couleurs
Modifiez les variables CSS dans `styles.css` pour changer les couleurs :
```css
:root {
    --primary-color: #4CAF50;
    --secondary-color: #45a049;
    --background-color: #ffffff;
    --text-color: #333333;
}
```

### Langues
Ajoutez ou modifiez les langues dans `index.html` :
```html
<select id="languageDropdown">
    <option value="en">English</option>
    <option value="ha">Haoussa</option>
    <option value="ee">Ewe</option>
    <option value="tw">Twi</option>
</select>
```

## Développement

Pour tester le widget localement :

1. Installez les dépendances :
```bash
npm install
```

2. Démarrez le serveur de développement :
```bash
npm start
```

3. Ouvrez `http://localhost:3000` dans votre navigateur

## Compatibilité

- Chrome 60+
- Firefox 55+
- Safari 11+
- Edge 79+

## Support

Pour toute question ou problème, veuillez ouvrir une issue sur le repository.

## Licence

MIT License 