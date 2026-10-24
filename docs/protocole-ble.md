# Protocole Bluetooth des bagues Sphero Specdrums

Reconstitué à partir de l'APK Specdrums Mix 1.2.2 (code Java décompilé + bibliothèque native `libCore.so`)
et validé sur deux bagues : SD-AABE (firmware 4.2.470) et SD-FC4A (firmware 3.1.262).

## Identification

- Nom Bluetooth : préfixe `SD-` (ex. `SD-AABE`).
- Protocole : **Sphero API v2** (même famille que BOLT / Mini / RVR).

| Service | Caractéristique | Rôle |
|---|---|---|
| `00010001-574f-4f20-5370-6865726f2121` | `00010002-…` | commandes API v2 (write + notify) |
| | `00010003-…` | « shell » (notify, inutilisé) |
| `00020001-574f-4f20-5370-6865726f2121` | `00020002-…` | contrôle DFU (write + notify) |
| | `00020004-…` | état DFU (read) |
| | `00020005-…` | anti-DOS (write) |

## Séquence de connexion (InitStrategySpheroMini)

1. Écrire `usetheforce...band` (ASCII) sur l'anti-DOS `00020005`.
2. S'abonner aux notifications (dont `00020002` **avant** toute écriture dessus).
3. **Si le service `00010001` est absent, la bague est dans son bootloader** (cas fréquent au réveil) :
   écrire l'octet `0x1E` sur `00020002` (« jump to main app »), attendre ~2,5 s, se reconnecter.
4. `POWER.wake` (13:0D), puis `IO.enableColorTapNotify(true)` (1A:1D, données `01`).
5. Facultatif : notifications batterie (13:1B `01`) et chargeur (13:20 `01`), palette (1A:47 `00` = usine).
6. Garder la connexion : `API.ping` (10:00) toutes les 2 s.

## Trame API v2

```
8D | flags | [tid] | [sid] | did | cid | seq | [err] | données… | checksum | D8
```

- flags : `0x01` réponse, `0x02` demande de réponse, `0x08` activité, `0x10` tid présent, `0x20` sid présent.
  Commande envoyée : flags `0x0A`.
- checksum = `~(somme des octets de flags à la fin des données) & 0xFF`.
- échappement : `AB`→`AB 23`, `8D`→`AB 05`, `D8`→`AB 50`.
- **Les écritures doivent être découpées en morceaux de 20 octets** (la bague refuse les écritures longues
  et redémarre si on lui envoie p. ex. la palette de 55 octets d'un bloc).
- Le firmware 3.x renvoie ses notifications octet par octet : il faut un lecteur de flux.

## Commandes utiles

| did:cid | Nom | Données |
|---|---|---|
| 10:00 | ping | — |
| 11:00 | version appli principale | réponse : 3 × uint16 (majeur, mineur, révision) |
| 13:0D | wake | — |
| 13:00 | deep sleep | — |
| 13:17 | état batterie | réponse : 1 OK, 2 faible, 3 critique |
| 13:1B | activer notif. batterie | `01` → notifications 13:1C |
| 13:1F | état chargeur | réponse : 1 débranché, 2 en charge, 3 chargé (branché) |
| 13:20 | activer notif. chargeur | `01` → notifications 13:21 |
| 13:19 / 13:1A | notif. « va s'endormir » / « s'est endormie » | — |
| 1A:1D | activer les taps couleur | `01` |
| **1A:1E** | **notification de tap** | `R G B confiance idCouleur intensité` |
| 1A:44 | lire la palette active | 12 × (index, R, G, B) |
| 1A:45 | écrire la palette active | 12 × (index, R, G, B) — firmware 4.x uniquement |
| 1A:47 | charger une palette | `00` usine, `01` MIDI — firmware 4.x uniquement |

### Notification de tap (1A:1E)

- `idCouleur` : 0 à 11 = couleur de la palette reconnue, `255` = couleur inconnue.
- `intensité` > 0 : tap ; `intensité` = 0 : doigt relevé (~100 ms plus tard), utile pour les sons « maintenus ».

### Palette d'usine (détection)

| # | R G B | Tapis |
|---|---|---|
| 0 | e4 35 40 | 1 rouge |
| 1 | fb ab 19 | 2 orange |
| 2 | fc ee 21 | 3 jaune |
| 3 | 74 c0 44 | 4 vert |
| 4 | 00 a1 82 | 5 turquoise |
| 5 | 00 7b c2 | 6 bleu |
| 6 | 7e 4f 9a | 7 violet |
| 7 | ca 57 a0 | 8 magenta |
| 8 | f6 92 78 | ▲ rose |
| 9 | fe c6 79 | ◆ pêche |
| 10 | b1 d8 9c | ★ vert d'eau |
| 11 | 87 9e cf | ⬢ bleu ciel |

## Comportements observés

- **Pendant la charge, la bague n'envoie aucun tap** et la connexion est instable : il faut la débrancher.
- Batterie critique → notification 13:1A puis extinction.
- Après une mise en veille, la bague redémarre dans son bootloader (voir étape 3).
