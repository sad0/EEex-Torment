
-- EEex-PTEE: French strings (X-en_US.lua of the Torment port; tutoiement, as Torment's own French UI)

----------
-- Menu --
----------

uiStrings["EEex_Options_TRANSLATION_Menu_TabTitle"] = "Menu"

uiStrings["EEex_Options_TRANSLATION_Menu_UniversalScrollbarPadCollapsing"] = "Marge de barre de défilement adaptative"

uiStrings["EEex_Options_TRANSLATION_Menu_UniversalScrollbarPadCollapsing_Description"] = [[
Supprime automatiquement la marge fixe de 16 pixels à droite des textes lorsque la barre de défilement est masquée.

Certains mods d'interface s'attendent à ce que cette marge soit toujours appliquée. Désactive cette option si tu constates des textes mal alignés.
]]

----------------------------
-- Miscellaneous Keybinds --
----------------------------

uiStrings["EEex_Options_TRANSLATION_Keybinds_TabTitle"] = "Raccourcis divers"

uiStrings["EEex_Options_TRANSLATION_Keybinds_OpenOptions"] = "Ouvrir les options"

uiStrings["EEex_Options_TRANSLATION_Keybinds_OpenOptions_Description"] = [[
Raccourci qui ouvre directement ce menu.
]]

uiStrings["EEex_Options_TRANSLATION_Keybinds_ToggleKeycodeOutput"] = "Afficher les codes de touche"

uiStrings["EEex_Options_TRANSLATION_Keybinds_ToggleKeycodeOutput_Description"] = [[
Active ou désactive l'affichage des codes de touche.

Lorsqu'il est actif, EEex affiche dans le journal de combat le code de chaque touche pressée.
]]

-------------
-- Modules --
-------------

uiStrings["EEex_Options_TRANSLATION_Modules_TabTitle"] = "Modules"

uiStrings["EEex_Options_TRANSLATION_Modules_EnableAttackInfo"] = "Activer le module Infos d'attaque"

uiStrings["EEex_Options_TRANSLATION_Modules_EnableAttackInfo_Description"] = [[
Active la fenêtre d'informations d'attaque.

Cette fenêtre s'ouvre et affiche diverses informations d'attaque lorsque le curseur d'attaque survole une créature.

Elle indique :

- les chances de toucher de chaque membre du groupe sélectionné contre la cible ;

- et, en option, si la cible est immunisée contre l'arme de chaque membre sélectionné.

Le sens de l'attaque peut être inversé en maintenant un raccourci (par défaut « Alt gauche »).

En sens inversé, la fenêtre affiche les informations d'attaque de la créature sous le curseur, comme si elle attaquait chaque membre sélectionné.
]]

uiStrings["EEex_Options_TRANSLATION_Modules_EnableEffectMenu"] = "Activer le module Menu des effets"

uiStrings["EEex_Options_TRANSLATION_Modules_EnableEffectMenu_Description"] = [[
Active le menu des effets.

Un menu listant tous les sorts qui affectent une créature s'affiche en maintenant un raccourci (par défaut « Maj gauche ») et en survolant cette créature.

Ce menu est construit dynamiquement : il fait de son mieux, mais il peut manquer certains effets et afficher parfois des sorts internes.
]]

uiStrings["EEex_Options_TRANSLATION_Modules_EnableEmptyContainer"] = "Activer le module Conteneurs vides"

uiStrings["EEex_Options_TRANSLATION_Modules_EnableEmptyContainer_Description"] = [[
Les conteneurs vides sont surlignés en gris au lieu du cyan habituel.
]]

uiStrings["EEex_Options_TRANSLATION_Modules_EnableScaleModule"] = "Activer le module Échelle"

uiStrings["EEex_Options_TRANSLATION_Modules_EnableScaleModule_Description"] = [[
Permet de choisir librement le facteur d'échelle de l'interface.
]]

uiStrings["EEex_Options_TRANSLATION_Modules_EnableTimeStep"] = "Activer le module Avance du temps"

uiStrings["EEex_Options_TRANSLATION_Modules_EnableTimeStep_Description"] = [[
Active un raccourci (par défaut « D ») qui, lorsque le jeu est en pause, fait avancer le temps du plus petit pas possible.

Le raccourci enlève la pause puis la remet presque aussitôt.

Le maintenir une demi-seconde fait s'écouler le temps jusqu'à ce que tu le relâches.
]]

uiStrings["EEex_Options_TRANSLATION_Modules_EnableTimerModule"] = "Activer le module Minuteurs"

uiStrings["EEex_Options_TRANSLATION_Modules_EnableTimerModule_Description"] = [[
Affiche à côté des portraits du groupe des indicateurs visuels de différents minuteurs.
]]

----------------------------
-- Module: Attack Info --
----------------------------

uiStrings["EEex_Options_TRANSLATION_AttackInfo_TabTitle"] = "Module : Infos d'attaque"

uiStrings["EEex_Options_TRANSLATION_AttackInfo_Enable"] = "Activé"

uiStrings["EEex_Options_TRANSLATION_AttackInfo_Enable_Description"] = uiStrings["EEex_Options_TRANSLATION_Modules_EnableAttackInfo_Description"]

uiStrings["EEex_Options_TRANSLATION_AttackInfo_FontPoint"] = "Taille de police"

uiStrings["EEex_Options_TRANSLATION_AttackInfo_FontPoint_Description"] = [[
Taille (en points) de la police utilisée pour les informations d'attaque.
]]

uiStrings["EEex_Options_TRANSLATION_AttackInfo_ImmunityDisplayType"] = "Affichage des immunités"

uiStrings["EEex_Options_TRANSLATION_AttackInfo_ImmunityDisplayType_Description"] = [[
Façon d'indiquer les immunités de la cible dans la fenêtre.

« Couleur » : change la couleur des pourcentages de toucher lorsque la cible est immunisée contre l'attaquant.

« Aucun » : n'affiche pas les immunités.

« Texte » : remplace les pourcentages de toucher lorsque la cible est immunisée contre l'attaquant.
]]

uiStrings["EEex_Options_TRANSLATION_AttackInfo_ImmunityDisplayType_Color"] = "Couleur"

uiStrings["EEex_Options_TRANSLATION_AttackInfo_ImmunityDisplayType_None"] = "Aucun"

uiStrings["EEex_Options_TRANSLATION_AttackInfo_ImmunityDisplayType_Text"] = "Texte"

uiStrings["EEex_Options_TRANSLATION_AttackInfo_ImmunityDisplayType_ShowColorKey"] = "Afficher la légende des couleurs"

uiStrings["EEex_Options_TRANSLATION_AttackInfo_ImmunityDisplayType_ShowColorKey_Description"] = [[
Affiche une légende des couleurs en haut à droite de la fenêtre lorsque « Affichage des immunités » vaut « Couleur ».
]]

uiStrings["EEex_Options_TRANSLATION_AttackInfo_OpenKeybind"] = "Raccourci d'ouverture"
uiStrings["EEex_Options_TRANSLATION_AttackInfo_OpenKeybind_Description"] = [[
Ce raccourci ouvre la fenêtre d'informations d'attaque.
]]

uiStrings["EEex_Options_TRANSLATION_AttackInfo_OpenWithAttackCursor"] = "Ouvrir avec le curseur d'attaque"
uiStrings["EEex_Options_TRANSLATION_AttackInfo_OpenWithAttackCursor_Description"] = [[
La fenêtre d'informations d'attaque s'ouvre automatiquement lorsque le curseur d'attaque survole une créature.
]]

uiStrings["EEex_Options_TRANSLATION_AttackInfo_ReverseKeybind"] = "Raccourci d'inversion"

uiStrings["EEex_Options_TRANSLATION_AttackInfo_ReverseKeybind_Description"] = [[
Lorsqu'il est pressé, ce raccourci inverse le sens de l'attaque dans la fenêtre :
elle affiche alors les chances de toucher de la cible contre les membres sélectionnés.

Ce raccourci peut ouvrir la fenêtre si elle est fermée.
]]

uiStrings["EEex_Options_TRANSLATION_AttackInfo_ShowColumnHeaders"] = "Afficher les en-têtes de colonnes"

uiStrings["EEex_Options_TRANSLATION_AttackInfo_ShowColumnHeaders_Description"] = [[
La première ligne de la liste affiche les en-têtes de colonnes.
]]

uiStrings["EEex_Options_TRANSLATION_AttackInfo_HideUnusedOffhandHeader"] = "Masquer l'en-tête de main secondaire inutilisé"

uiStrings["EEex_Options_TRANSLATION_AttackInfo_HideUnusedOffhandHeader_Description"] = [[
Masque l'en-tête de la colonne de main secondaire lorsque la vue actuelle n'a rien à y afficher.
]]

uiStrings["EEex_TRANSLATION_AttackInfo_PartyAttacksTarget"] = "Le groupe attaque la cible"

uiStrings["EEex_TRANSLATION_AttackInfo_TargetAttacksParty"] = "La cible attaque le groupe"

uiStrings["EEex_TRANSLATION_AttackInfo_ImmuneColorKey"] = "Immunisé = "

uiStrings["EEex_TRANSLATION_AttackInfo_Mainhand"] = "Principale"

uiStrings["EEex_TRANSLATION_AttackInfo_Offhand"] = "Secondaire"

----------------------------
-- Module: Effect Menu --
----------------------------

uiStrings["EEex_Options_TRANSLATION_EffectMenu_TabTitle"] = "Module : Menu des effets"

uiStrings["EEex_Options_TRANSLATION_EffectMenu_LaunchKeybind"] = "Raccourci d'ouverture"

uiStrings["EEex_Options_TRANSLATION_EffectMenu_LaunchKeybind_Description"] = [[
Le menu des effets s'ouvre lorsque ce raccourci est maintenu et que la souris survole une créature.
]]

uiStrings["EEex_Options_TRANSLATION_EffectMenu_RowCount"] = "Nombre de lignes"

uiStrings["EEex_Options_TRANSLATION_EffectMenu_RowCount_Description"] = [[
Nombre de lignes affichées par le menu des effets.
]]

-------------------
-- Module: Scale --
-------------------

uiStrings["EEex_Options_TRANSLATION_Scale_TabTitle"] = "Module : Échelle"

uiStrings["EEex_Options_TRANSLATION_Scale_Percentage"] = "Échelle de l'interface [0-100]"

uiStrings["EEex_Options_TRANSLATION_Scale_Percentage_Description"] = [[
Impose au moteur le facteur d'échelle d'interface indiqué.

La valeur est un pourcentage entier entre 0 et 100.

Par exemple, « 50 » impose une échelle de 50 %.
]]

-----------------------
-- Module: Time Step --
-----------------------

uiStrings["EEex_Options_TRANSLATION_TimeStep_TabTitle"] = "Module : Avance du temps"

uiStrings["EEex_Options_TRANSLATION_TimeStep_Keybind"] = "Raccourci d'avance du temps"

uiStrings["EEex_Options_TRANSLATION_TimeStep_Keybind_Description"] = [[
Lorsque le jeu est en pause, ce raccourci fait avancer le temps du plus petit pas possible.

Le raccourci enlève la pause puis la remet presque aussitôt.

Le maintenir une demi-seconde fait s'écouler le temps jusqu'à ce que tu le relâches.
]]

-------------------
-- Module: Timer --
-------------------

uiStrings["EEex_Options_TRANSLATION_Timer_TabTitle"] = "Module : Minuteurs"

uiStrings["EEex_Options_TRANSLATION_Timer_HugPortraits"] = "Coller aux portraits"

uiStrings["EEex_Options_TRANSLATION_Timer_HugPortraits_Description"] = [[
Supprime l'espace entre les barres de minuteur et leur portrait.
]]

uiStrings["EEex_Options_TRANSLATION_Timer_ShowCastTimer"] = "Minuteur d'incantation"

uiStrings["EEex_Options_TRANSLATION_Timer_ShowCastTimer_Description"] = [[
Affiche une barre cyan à côté des portraits du groupe.

Cet indicateur montre le temps de recharge avant de pouvoir utiliser à nouveau un sort ou un objet.
]]

uiStrings["EEex_Options_TRANSLATION_Timer_ShowContingencyTimer"] = "Minuteur de contingence"

uiStrings["EEex_Options_TRANSLATION_Timer_ShowContingencyTimer_Description"] = [[
Affiche une barre verte à côté des portraits du groupe.

Cet indicateur montre l'intervalle de vérification des conditions de contingence.

Certains mods ajoutent en coulisse des effets de contingence pour certains comportements : l'indicateur peut alors apparaître de façon inattendue.
]]

uiStrings["EEex_Options_TRANSLATION_Timer_ShowModalTimer"] = "Minuteur de mode"

uiStrings["EEex_Options_TRANSLATION_Timer_ShowModalTimer_Description"] = [[
Affiche une barre rouge à côté des portraits du groupe.

Cet indicateur montre l'intervalle des actions de mode (recherche de pièges, renvoi des morts-vivants, etc.).
]]

---------------
-- Uncap FPS --
---------------

uiStrings["EEex_Options_TRANSLATION_UncapFPS_TabTitle"] = "Déblocage des IPS"

uiStrings["EEex_Options_TRANSLATION_UncapFPS_AISpeed"] = "Vitesse de l'IA"

uiStrings["EEex_Options_TRANSLATION_UncapFPS_AISpeed_Description"] = [[
Nombre de fois par seconde où la « logique » du jeu est mise à jour.

Elle détermine la vitesse du jeu.
]]

uiStrings["EEex_Options_TRANSLATION_UncapFPS_Enable"] = "Débloquer les IPS"

uiStrings["EEex_Options_TRANSLATION_UncapFPS_Enable_Description"] = [[
Supprime la limite d'images par seconde habituelle du moteur : le jeu s'affiche à la fréquence de rafraîchissement de ton écran.

Les déplacements de la vue sont plus fluides sur les écrans à haute fréquence.
]]

uiStrings["EEex_Options_TRANSLATION_UncapFPS_EnableFPSLimit"] = "Activer la limite d'IPS"

uiStrings["EEex_Options_TRANSLATION_UncapFPS_EnableFPSLimit_Description"] = [[
Active l'option « Limite d'IPS ».
]]

uiStrings["EEex_Options_TRANSLATION_UncapFPS_FPSLimit"] = "Limite d'IPS"

uiStrings["EEex_Options_TRANSLATION_UncapFPS_FPSLimit_Description"] = [[
Limite les images par seconde débloquées à la valeur indiquée.
]]

uiStrings["EEex_Options_TRANSLATION_UncapFPS_FPSLimitBusyWaitThreshold"] = "Seuil d'attente active"

uiStrings["EEex_Options_TRANSLATION_UncapFPS_FPSLimitBusyWaitThreshold_Description"] = [[
Si la prochaine image est prévue dans moins de ce nombre de millisecondes, le moteur attend activement
au lieu de libérer le processeur.

Ne s'applique que lorsque l'option « Débloquer les IPS » est active.

Une valeur plus élevée régularise l'affichage, au prix d'une charge processeur plus forte.

La valeur « 0 » désactive la libération du processeur. Ne l'utilise que sur un appareil très peu puissant.
]]

uiStrings["EEex_Options_TRANSLATION_UncapFPS_FullscreenVRR"] = "Indice de rafraîchissement variable (plein écran)"

uiStrings["EEex_Options_TRANSLATION_UncapFPS_FullscreenVRR_Description"] = [[
Indique au système d'IPS débloquées que le pilote graphique activera le rafraîchissement variable (VRR) en plein écran.

La boucle de jeu s'adapte alors automatiquement au VRR.

Active cette option seulement si le VRR est réellement actif sur ton système : sinon, elle dégrade l'affichage.
]]

uiStrings["EEex_Options_TRANSLATION_UncapFPS_LuaGCSteps"] = "Étapes de nettoyage mémoire Lua"

uiStrings["EEex_Options_TRANSLATION_UncapFPS_LuaGCSteps_Description"] = [[
Temps que Lua consacre, après chaque image, à libérer la mémoire inutilisée.

Une valeur basse donne plus d'IPS, mais peut provoquer des saccades quand beaucoup de « déchets » s'accumulent.

Une valeur haute évite les saccades, au prix d'un IPS plus bas.

Une valeur extrêmement haute peut prendre trop de temps et dérégler le rythme des images.
]]

uiStrings["EEex_Options_TRANSLATION_UncapFPS_RemoveMiddleMouseScrollMultiplier"] = "Supprimer le multiplicateur du clic molette"

uiStrings["EEex_Options_TRANSLATION_UncapFPS_RemoveMiddleMouseScrollMultiplier_Description"] = [[
Supprime le multiplicateur fixe appliqué au déplacement de la vue en maintenant le bouton central de la souris.
]]

uiStrings["EEex_Options_TRANSLATION_UncapFPS_VSyncEnabled"] = "Synchronisation verticale"

uiStrings["EEex_Options_TRANSLATION_UncapFPS_VSyncEnabled_Description"] = [[
Synchronise automatiquement l'affichage du jeu avec l'écran.

Supprime les déchirures d'image, au prix d'une latence de commande un peu plus élevée.
]]

-------------------
-- Miscellaneous --
-------------------

uiStrings["B3EffectMenu_TRANSLATION_No_Name"]              = "(Sans nom)"
uiStrings["EEex_Options_TRANSLATION_Accept"]               = "Valider"
uiStrings["EEex_Options_TRANSLATION_EEex_Options"]         = "Options EEex"
uiStrings["EEex_Options_TRANSLATION_Exit"]                 = "Quitter"
uiStrings["EEex_Options_TRANSLATION_Locked"]               = "(Verrouillé)"
uiStrings["EEex_Options_TRANSLATION_On_Sequence_Pressed"]  = "À l'appui de la séquence"
uiStrings["EEex_Options_TRANSLATION_On_Sequence_Released"] = "Au relâchement de la séquence"
uiStrings["EEex_Options_TRANSLATION_Requires_Restart"]     = "Redémarrage requis"
uiStrings["EEex_Options_TRANSLATION_Reset_to_Default"]     = "Valeur par défaut"
uiStrings["EEex_Options_TRANSLATION_Reset_All_to_Default"] = "Réinitialiser"
uiStrings["EEex_Options_TRANSLATION_Reset_All_Confirm"]    = "Rétablir toutes les options EEex à leur valeur par défaut ?"

uiStrings["EEex_Options_TRANSLATION_Description_Hint"] = [[
Clique sur le nom d'une option pour afficher sa description.
]]
