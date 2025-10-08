# Guide de Test - Assistant Promogo

Ce document fournit des exemples de test pour chaque intention (intent) supportée par l'assistant Promogo. Les tests sont organisés par langue : Anglais (en), Hausa (ha), Ewe (ee) et Twi (tw).

## 1. Achat (buy)

### Anglais
- I want to buy rice
- I need to purchase a phone
- Can I buy some vegetables?
- I'm looking to buy a car
- How can I buy this product?

### Hausa
- Ina son sayen shinkafa
- Ina bukatar sayen waya
- Zan iya sayen kayan lambu?
- Ina neman sayen mota
- Ta yaya zan iya sayen wannan kaya?

### Ewe
- Mele dii be yeaƒle dɔ
- Mehiã be yeaƒle telefon
- Mate ŋu aƒle atsiwo?
- Mele dii be yeaƒle lɔ̃
- Aleke mate ŋu aƒle nu sia?

### Twi
- Mepɛ sɛ metɔ ɛmo
- Mehiã sɛ metɔ phone
- Metumi atɔ nhaban?
- Mepɛ sɛ metɔ car
- Ɔkwan bɛn so na metumi atɔ nneɛma yi?

## 2. Vente (sell)

### Anglais
- I want to sell my phone
- I need to list my car for sale
- Can I sell some clothes?
- How do I sell my products?
- I want to become a seller

### Hausa
- Ina son sayar da wayata
- Ina bukatar sayar da motata
- Zan iya sayar da tufafi?
- Ta yaya zan iya sayar da kayana?
- Ina son zama mai sayarwa

### Ewe
- Mele dii be yeadzra nye telefon
- Mehiã be yeadzra nye lɔ̃
- Mate ŋu adzra nukoko?
- Aleke mate ŋu adzra nye nuwo?
- Mele dii be yeaɖo dzrala

### Twi
- Mepɛ sɛ metɔn me phone
- Mehiã sɛ metɔn me car
- Metumi atɔn me ntoma?
- Ɔkwan bɛn so na metumi atɔn me nneɛma?
- Mepɛ sɛ meyɛ ɔtɔnfo

## 3. Support client (contact_support)

### Anglais
- I need help
- Can you help me?
- I want to talk to customer service
- I have a problem
- How can I contact support?

### Hausa
- Ina bukatar taimako
- Za ka iya taimaka mini?
- Ina son magana da ma'aikatan tallafin
- Ina da matsala
- Ta yaya zan iya tuntuɓar tallafin?

### Ewe
- Mehiã kpekpeɖeŋu
- Àte ŋu akpe ɖe ŋuwò?
- Mele dii be yeaɖo kpekpeɖeŋu hatso ŋu
- Mele dii be yeaɖo nya
- Aleke mate ŋu ade kpekpeɖeŋu hatso ŋu?

### Twi
- Mehiã mmoa
- Wobɛtumi aboa me?
- Mepɛ sɛ meka kasa ne customer service
- Mewɔ nsɛm
- Ɔkwan bɛn so na metumi aka customer service?

## 4. Inscription/Connexion (signup/login)

### Anglais
- I want to create an account
- How do I sign up?
- I need to log in
- Can I create a new account?
- How do I access my account?

### Hausa
- Ina son ƙirƙiran account
- Ta yaya zan iya yin rajista?
- Ina bukatar shiga
- Zan iya ƙirƙiran sabon account?
- Ta yaya zan iya shiga account ɗina?

### Ewe
- Mele dii be yeaɖo akɔnt
- Aleke mate ŋu aɖo akɔnt?
- Mehiã be yeaʋu akɔnt
- Mate ŋu aɖo akɔnt yeye?
- Aleke mate ŋu aʋu akɔnt le?

### Twi
- Mepɛ sɛ meyɛ account
- Ɔkwan bɛn so na metumi ayɛ account?
- Mehiã sɛ mekɔ account mu
- Metumi ayɛ account foforɔ?
- Ɔkwan bɛn so na metumi ahwɛ me account?

## 5. Applications (seller/buyer/delivery)

### Anglais
- I want to use the seller app
- How do I access the buyer app?
- Show me the delivery app
- Where can I find the seller app?
- How do I use the buyer app?

### Hausa
- Ina son amfani da app ɗin mai sayarwa
- Ta yaya zan iya shiga app ɗin mai saya?
- Nuna mini app ɗin isar da kaya
- Ina zan iya samun app ɗin mai sayarwa?
- Ta yaya zan iya amfani da app ɗin mai saya?

### Ewe
- Mele dii be yeazã dzrala ƒe app
- Aleke mate ŋu aʋu nuƒlela ƒe app?
- Kpɔ ɖoɖo ƒe app
- Afika mate ŋu akpɔ dzrala ƒe app?
- Aleke mate ŋu azã nuƒlela ƒe app?

### Twi
- Mepɛ sɛ mehwɛ seller app
- Ɔkwan bɛn so na metumi ahwɛ buyer app?
- Kyerɛ me delivery app
- Ɛhe na metumi ahunu seller app?
- Ɔkwan bɛn so na metumi ade buyer app?

## Notes pour les testeurs

1. **Test multilingue**
   - Tester chaque intention dans toutes les langues supportées
   - Vérifier que les réponses sont dans la bonne langue
   - Confirmer que l'assistant maintient la langue choisie

2. **Test des formulaires**
   - Vérifier le processus d'achat complet
   - Vérifier le processus de vente complet
   - Tester les validations de champs

3. **Test des redirections**
   - Vérifier les liens vers les applications
   - Tester les redirections de connexion/inscription
   - Confirmer les liens de support

4. **Test des réponses**
   - Vérifier la pertinence des réponses
   - Confirmer la présence des boutons appropriés
   - Tester les messages d'erreur

5. **Test de performance**
   - Vérifier le temps de réponse
   - Tester la gestion des erreurs
   - Confirmer la stabilité du système 