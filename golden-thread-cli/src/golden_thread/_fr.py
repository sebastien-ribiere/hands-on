"""French presentation catalogue. Never used to produce evidence or policy digests."""

TEXT = {
    '{0}method    {1}':
        '{0}méthode   {1}',
    '{0}tool      {1}':
        '{0}outil     {1}',
    '{0}recorded  {1}':
        '{0}date      {1}',
    'PATH STATUS   {0}':
        'ÉTAT DU CHEMIN {0}',
    'Golden Thread attached':
        'Projet rattaché à Golden Thread',
    'Manifest      {0}':
        'Manifest      {0}',
    'Next          {0}':
        'Suite         {0}',
    'Required sections in an assessment:':
        'Sections requises dans une évaluation :',
    '{0}  assessment recorded':
        '{0}  évaluation enregistrée',
    "This is one reader's assessment of a document, not a measurement.":
        'Ce score est l’opinion argumentée d’un lecteur sur le document.',
    'It satisfies nothing on its own.':
        'Il ne suffit pas à satisfaire la DoR.',
    'Next          golden-thread verify':
        'Suite         golden-thread verify',
    'This records that YOU {0} this mission, on your own reading.':
        'Vous enregistrez VOTRE décision sur cette mission : {0}.',
    'The score above is an opinion; it has approved nothing.':
        'Le score est une opinion. L’approbation reste votre décision.',
    '{0}  human attestation recorded':
        '{0}  attestation humaine enregistrée',
    'This records that YOU {0} this, on your own account.':
        'Vous enregistrez VOTRE déclaration : {0}.',
    'Nothing here checked it. Nothing here can: that is why this':
        'Cet outil ne vérifie pas que l’action a eu lieu.',
    'requirement is satisfied by a name rather than by a verdict.':
        'L’exigence repose sur votre déclaration nominative.',
    '{0}  attestation recorded':
        '{0}  attestation enregistrée',
    'This records that this document was stamped against this exact':
        'Le stamp relie ce document à cette version exacte du code.',
    'code. It is not a claim that the documentation is correct: nothing':
        'Il ne garantit pas la justesse de la documentation.',
    'here read it, and nothing here could tell you if it were wrong.':
        'Sa lecture et son appréciation restent humaines.',
    '{0}subject   recorded {1}{2}':
        '{0}sujet     enregistré {1}{2}',
    '{0}subject   {1}/ - {2}{3}':
        '{0}sujet     {1}/ - {2}{3}',
    '{0}rests on  {1}: {2}':
        '{0}s’appuie sur {1} : {2}',
    '{0}never verified':
        '{0}jamais vérifié',
    '{0}recorded {1} no longer applies:':
        '{0}le résultat enregistré {1} ne s’applique plus :',
    'Nothing verified yet. Run: golden-thread verify':
        'Aucune vérification effectuée. Lancez : golden-thread verify',
    '  {0}  ({1} pt)  {2}':
        '  {0}  ({1} pt)  {2}',
    'Nothing was recorded.':
        'Rien n’a été enregistré.',
    'Attach a project to a versioned Golden Thread and verify it.':
        'Rattacher un projet à un Golden Thread versionné et le vérifier.',
    'project directory (default: current directory)':
        'répertoire du projet (par défaut : répertoire courant)',
    'attach this project to a Golden Thread':
        'rattacher ce projet à un Golden Thread',
    'Git repository of the Golden Thread':
        'dépôt Git du Golden Thread',
    'tag or branch to pin, e.g. v0.1.0':
        'tag ou branche à fixer, par exemple v0.1.0',
    "profile to use (default: the source's own)":
        'profil à utiliser (par défaut : celui de la source)',
    'report the evidence on record':
        'afficher les preuves enregistrées',
    'machine-readable report':
        'rapport JSON',
    "produce evidence for the profile's requirements":
        'produire les preuves des exigences du profil',
    'the Definition of Ready: publish the rubric, record an assessment, record a human decision':
        'Definition of Ready : afficher la grille, enregistrer une évaluation et une décision humaine',
    'machine-readable rubric':
        'grille au format JSON',
    'JSON assessment file, or - for stdin':
        'fichier JSON d’évaluation, ou - pour l’entrée standard',
    'who is deciding (default: git user.email)':
        'identité de la personne qui décide (par défaut : git user.email)',
    "why, in the attestor's own words":
        'motif, dans les mots de la personne qui atteste',
    'record a refusal rather than an approval':
        'enregistrer un refus',
    'the confirmation phrase, for use where no terminal is attached. Recording an approval this way still records it as yours':
        'phrase de confirmation sans terminal ; l’approbation reste enregistrée en votre nom',
    "record a claim no tool can check, for a requirement satisfied by a person's word":
        'enregistrer une déclaration humaine pour une exigence qu’aucun outil ne peut vérifier',
    'which requirement (only needed if the profile has more than one)':
        'exigence concernée (si le profil en contient plusieurs)',
    'who is claiming (default: git user.email)':
        'identité de la personne qui atteste (par défaut : git user.email)',
    'anything worth recording alongside it':
        'commentaire à conserver avec la déclaration',
    'record that this is NOT the case, rather than that it is':
        'déclarer que l’exigence n’a pas été satisfaite',
    'the confirmation phrase, for use where no terminal is attached. Recording an attestation this way still records it as yours':
        'phrase de confirmation sans terminal ; l’attestation reste enregistrée en votre nom',
    'print the claim and the confirmation phrase, and record nothing':
        'afficher la déclaration et sa confirmation, sans rien enregistrer',
    'the documentation requirement: stamp a document':
        'documentation : relier un document au code courant par un stamp',
    'record which version of the code this document describes':
        'enregistrer la version du code décrite par ce document',
    'which documentation requirement (only needed if the profile has more than one)':
        'exigence documentaire concernée (si le profil en contient plusieurs)',
    '{0}          current  {1}{2}':
        '{0}          courant    {1}{2}',
    '{0}could not run: {1}':
        '{0}exécution impossible : {1}',
    'Evidence exists but no longer describes this project, so it is':
        'Des preuves existent, mais leur sujet ou leur exigence a changé.',
    'not shown as a verdict. Run: golden-thread verify':
        'Vérifiez à nouveau avant de conclure : golden-thread verify',
    'which readiness requirement (only needed if the profile has more than one)':
        'exigence de readiness concernée (si le profil en contient plusieurs)',
    'print the versioned rubric this profile pins':
        'afficher la grille versionnée de ce profil',
    'record an assessment produced against the rubric':
        'enregistrer une évaluation fondée sur la grille',
    'record a human decision on the recorded assessment':
        'enregistrer une décision humaine sur l’évaluation',
    'golden-thread: {0}':
        'golden-thread : {0}',
    'A readiness requirement is not satisfied: this work was not agreed':
        'Une exigence de readiness n’est pas satisfaite.',
    'before it started. Like every other Golden Thread signal, it is a':
        'Le rapport précise ce qui manque et sur quelles déclarations il repose.',
    'signal -- nothing here stops you writing code. It states that the':
        'La CLI laisse les modifications possibles ; la DoR reste non satisfaite.',
    'Definition of Ready has not been met, and by whose account.':
        'Résolvez les manques ou décidez explicitement de continuer hors-piste.',
    'Next          golden-thread readiness rubric':
        'Suite         golden-thread readiness rubric',
    '{0} requirement(s) not satisfied, {1} located in the code.':
        '{0} exigence(s) non satisfaite(s), {1} écart(s) localisé(s) dans le code.',
    'This is a signal, not a block: you may stay off path deliberately, but the':
        'Vous pouvez choisir de poursuivre hors-piste.',
    'deviation is now explicit.':
        'L’écart reste visible dans le rapport.',
    'Policy ref':
        'Réf. policy',
    'Policy SHA':
        'SHA policy',
    'Profile':
        'Profil',
    'Requirements':
        'Exigences',
    'Rubric':
        'Grille',
    'Subject':
        'Sujet',
    'Threshold':
        'Seuil',
    'Blockers':
        'Blockers',
    'Decisions':
        'Décisions',
    'Approval':
        'Approbation',
    'Assessor':
        'Évaluateur',
    'Assessment':
        'Évaluation',
    'Attestor':
        'Attestateur',
    'Decision':
        'Décision',
    'Claim':
        'Déclaration',
    'Confirm with':
        'Confirmation',
    'Describes':
        'Décrit',
    'Stamp':
        'Stamp',
    'none':
        'aucune',
    'at most {0}':
        'au plus {0}',
    'a human decision is required':
        'décision humaine obligatoire',
    'not required':
        'non requise',
    'stamped':
        'stamp enregistré',
    'already current':
        'stamp déjà à jour',
    'approved':
        'approuvée',
    'rejected':
        'rejetée',
    'attested':
        'attestée',
    'refused':
        'refusée',
    'assessment':
        'évaluation',
    'human-attestation':
        'attestation humaine',
    'blocker':
        'blocker',
    'decision':
        'décision',
    '{0} file(s) sha256:{1}':
        '{0} fichier(s) sha256:{1}',
    ', dirty':
        ', modifications locales',
    "   [below this profile's threshold]":
        '   [sous les seuils de ce profil]',
    '{0}/{1} by {2}':
        '{0}/{1} par {2}',
    'A mission is Ready before implementation starts':
        'La mission est prête avant le début de l’implémentation',
    'The test suite passes':
        'La suite de tests passe',
    'Protection spells must not depend on Fire':
        'Les sorts de protection ne doivent pas dépendre de Fire',
    'No known security defect at MEDIUM or above':
        'Aucun défaut de sécurité signalé à partir du seuil MEDIUM',
    'The documentation describes the code that ships':
        'La documentation décrit le code livré',
    'Cookies were prepared and shared with the team':
        'Les cookies ont été préparés et partagés avec l’équipe',
    'Cookies have been prepared and shared with the team for this delivery.':
        'Des cookies ont été préparés et partagés avec l’équipe pour cette livraison.',
    'Type the phrase to confirm: {0}':
        'Saisissez la phrase pour confirmer : {0}',
    'Is this mission ready to be worked on?':
        'Cette mission est-elle prête à être réalisée ?',
    'The problem, and whose problem it is':
        'Le problème et les personnes concernées',
    'Is the problem stated, rather than a solution stated in its place?\nIs it clear who currently has this problem?':
        'Le problème est-il formulé, au-delà d’une solution proposée ?\nSait-on qui rencontre ce problème ?',
    'An observable outcome':
        'Un résultat observable',
    'Could someone tell, from the outside, whether this was done?\nAre there acceptance criteria, or only intentions?':
        'Peut-on constater de l’extérieur que la mission est accomplie ?\nExiste-t-il des critères d’acceptation observables ?',
    'A drawn boundary':
        'Un périmètre explicite',
    'Is what is IN scope stated?\nIs what is deliberately OUT of scope stated? An unstated boundary is the\nmost common cause of a mission growing after it starts.':
        'Le périmètre inclus est-il défini ?\nLes exclusions sont-elles explicites ? Une limite implicite peut faire grossir la mission.',
    'Constraints, including the ones the golden path imposes':
        'Les contraintes, y compris celles du chemin supporté',
    'Are the technical constraints named?\nDoes the mission acknowledge the architecture requirements its profile\nenforces, where they bear on the work?':
        'Les contraintes techniques sont-elles nommées ?\nLa mission tient-elle compte des exigences d’architecture applicables ?',
    'Named unknowns, and no hidden blockers':
        'Les inconnues et les blockers',
    'Are the open questions written down rather than left to be discovered?\nAre the decisions that need a human answer separated from the ones the\nimplementer can take alone?':
        'Les questions ouvertes sont-elles écrites ?\nLes décisions humaines sont-elles distinguées des choix que l’agent peut faire seul ?',
    'This rubric produces an ASSESSMENT, not a measurement.\n\nTwo assessors reading the same mission against this same rubric will disagree,\nand the same assessor asked twice may disagree with itself. The dimensions\nbelow make a score arguable -- they do not make it reproducible, and nothing\nin this rubric should be read as implying that 8/10 is a property of the\ndocument rather than an opinion about it.\n\nThe score exists to structure a conversation with a human being, and to make\nthe gaps in a mission explicit before anyone writes code against them. It is\nnever, on its own, permission to start.':
        'Cette grille produit une ÉVALUATION, pas une mesure.\n\nDeux lecteurs peuvent attribuer des scores différents à la même mission ;\nun même lecteur peut aussi changer d’avis. Les dimensions rendent le score\ndiscutable et argumenté. Elles ne le rendent pas reproductible : 8/10 est\nune opinion sur le document.\n\nLe score sert à préparer une discussion avec un humain et à rendre les\nmanques explicites avant de coder. Il n’autorise jamais à commencer seul.',
}

RECORDED = {
    'never verified':
        'jamais vérifié',
    'ran `{0}` over {1} file(s)':
        'commande exécutée : `{0}` sur {1} fichier(s)',
    'this profile fails on {0} and above, at {1} confidence and above':
        'seuil d’échec : sévérité {0} ou supérieure, avec une confiance {1} ou supérieure',
    '{0} further finding(s) recorded below that threshold, not counted as a failure here':
        '{0} autre(s) diagnostic(s) enregistré(s) sous ces seuils, sans échec pour ce profil',
    'bandit reported no findings at any severity':
        'Bandit n’a signalé aucun défaut, quelle que soit la sévérité',
    'ran `{0}` in {1}/, exit {2}':
        'commande exécutée : `{0}` dans {1}/, code de sortie {2}',
    'the command reported:':
        'sortie brute de la commande :',
    "layer '{0}' must not depend on {1}":
        'la couche « {0} » ne doit pas dépendre de {1}',
    "layer '{0}' may only depend on {1}":
        'la couche « {0} » peut uniquement dépendre de {1}',
    'no readiness assessment on record. Run: golden-thread readiness rubric':
        'aucune évaluation de readiness enregistrée. Lancez : golden-thread readiness rubric',
    'no human approval on record. A readiness score never approves itself. Run: golden-thread readiness approve':
        'aucune approbation humaine enregistrée. Le score ne vaut pas approbation. Après relecture, l’humain exécute : golden-thread readiness approve',
    'the recorded assessment carries no score':
        'l’évaluation enregistrée ne contient aucun score',
    'assessed at {0}/10, below the {1} this profile requires':
        'score évalué à {0}/10, sous le seuil de {1} requis par ce profil',
    '{0} decision(s) still awaiting a human answer':
        '{0} décision(s) attendent encore une réponse humaine',
    '{0} blocker(s), and this profile allows {1}: {2}':
        '{0} blocker(s), pour un maximum autorisé de {1} : {2}',
    'assessed at {0}/10 against {1}, at or above the {2} this profile requires':
        'score évalué à {0}/10 selon {1}, au moins égal au seuil de {2}',
    'approved by {0}':
        'approbation enregistrée par {0}',
    'an acceptable score and a human decision were both required; neither would have been enough alone':
        'le score recevable et la décision humaine sont tous deux présents ; les deux étaient requis',
    'no mission document found: expected {0}':
        'aucun document de mission trouvé ; attendu : {0}',
    'the {0} was made about a different version of the mission ({1} file(s) {2} -> {3})':
        'la déclaration {0} porte sur une autre version de la mission ({1} fichier(s) {2} -> {3})',
    'the {0} was made under rubric {1}, and this profile now pins {2}':
        'la déclaration {0} utilisait la grille {1} ; ce profil référence désormais {2}',
    "{0} recorded '{1}': {2}":
        '{0} a enregistré « {1} » : {2}',
    "{0} recorded '{1}'":
        '{0} a enregistré « {1} »',
    '{0} does not exist':
        '{0} n’existe pas',
    '{0} carries no golden-thread stamp, so it makes no claim about which code it describes':
        '{0} ne contient aucun stamp Golden Thread indiquant la version du code décrite',
    'expected a line: {0}':
        'ligne attendue : {0}',
    'Run: golden-thread docs stamp':
        'Après relecture humaine : golden-thread docs stamp',
    '{0} claims to describe {1}/, and this requirement is about {2}/':
        '{0} déclare décrire {1}/ ; cette exigence porte sur {2}/',
    '{0} describes {1}/ at {2}':
        '{0} décrit {1}/ à la version {2}',
    '{0}/ is now at {1}':
        '{0}/ est maintenant à la version {1}',
    'the code moved and the documentation did not say so':
        'le code a changé sans que le stamp documentaire le reflète',
    'read it, bring it up to date, then: golden-thread docs stamp':
        'relisez et mettez la documentation à jour, puis exécutez vous-même : golden-thread docs stamp',
    '{0} is stamped against {1}/ at {2}, which is what is there now':
        'le stamp de {0} vise {1}/ à la version courante {2}',
    'this records that the document was re-stamped against this exact code. It is not a claim that the prose is correct: nothing here read it':
        'le stamp correspond à ce code exact ; ce contrôle ne vérifie ni la lecture ni la justesse de la documentation',
    'the claim: Cookies have been prepared and shared with the team for this delivery.':
        'déclaration : des cookies ont été préparés et partagés avec l’équipe pour cette livraison.',
    'nobody has attested this, and nothing here can attest it on their behalf':
        'personne ne l’a attesté ; l’outil ne peut pas le faire à sa place',
    'Run: golden-thread attest {0}':
        'Si l’action a réellement eu lieu, l’humain exécute : golden-thread attest {0}',
    'the work moved on; the claim did not move with it':
        'le travail a changé ; la déclaration ne porte plus sur cette version',
    '{0} attested this about a different version of the work ({1} file(s) {2} -> {3} file(s) {4})':
        '{0} a attesté cela pour une autre version du travail ({1} fichier(s) {2} -> {3} fichier(s) {4})',
    'attested by {0}':
        'attestation enregistrée par {0}',
    'recorded on their word alone. Golden Thread verified that somebody said it, not that it happened':
        'Golden Thread vérifie la présence de cette déclaration nominative ; la réalisation de l’action repose sur la parole de son auteur',
    'the code changed: {0} file(s) {1} -> {2} file(s) {3}':
        'le code a changé : {0} fichier(s) {1} -> {2} fichier(s) {3}',
    'the requirement changed: {0} -> {1}':
        'l’exigence a changé : {0} -> {1}',
    'legacy evidence has no requirement fingerprint and the Golden Thread version changed: {0}':
        'l’ancienne preuve ne contient pas d’empreinte de l’exigence et la version Golden Thread a changé : {0}',
    'legacy evidence has no requirement fingerprint and the profile changed: {0} -> {1}':
        'l’ancienne preuve ne contient pas d’empreinte de l’exigence et le profil a changé : {0} -> {1}',
    'no Golden Thread manifest at {0}':
        'aucun manifest Golden Thread à l’emplacement {0}',
    'run: golden-thread init --source <repo> --ref <tag>':
        'lancez : golden-thread init --source <repo> --ref <tag>',
    'project directory does not exist: {0}':
        'le répertoire du projet n’existe pas : {0}',
    'there is no readiness assessment to decide on. Run: golden-thread readiness rubric':
        'aucune évaluation de readiness disponible pour décider. Lancez : golden-thread readiness rubric',
    'the recorded assessment was made about a different version of the mission ({0} -> {1}). Re-assess before deciding':
        'l’évaluation porte sur une autre version de la mission ({0} -> {1}). Réévaluez avant de décider',
    'the recorded assessment was made under rubric {0}, and this profile now pins {1}. Re-assess first':
        'l’évaluation utilisait la grille {0} ; ce profil référence désormais {1}. Réévaluez d’abord',
    'confirmation does not match. Expected: {0}':
        'la confirmation ne correspond pas. Phrase attendue : {0}',
    'confirmation does not match. Nothing recorded':
        'la confirmation ne correspond pas. Rien n’a été enregistré',
    'approval needs a person. There is no terminal attached here, so nothing can be typed.':
        'l’approbation demande une personne. Aucun terminal n’est attaché pour saisir sa confirmation.',
    'an attestation needs a person. There is no terminal attached here, so nothing can be typed.':
        'l’attestation demande une personne. Aucun terminal n’est attaché pour saisir sa confirmation.',
    'To record this non-interactively, pass: --confirm {0}':
        'Pour un enregistrement sans saisie interactive : --confirm {0}',
    "Doing so records it as yours. It does not make it anyone else's.":
        'La déclaration reste enregistrée en votre nom.',
    '`{0}` did not produce a readable report: {1}':
        '`{0}` n’a pas produit de rapport lisible : {1}',
    'bandit could not scan every file, so this is not a clean result: {0}':
        'Bandit n’a pas pu analyser tous les fichiers ; le contrôle ne peut pas conclure à un résultat conforme : {0}',
    'there is no {0}':
        'le document {0} est absent',
    'the golden path expects this project to document {0}/ there':
        'le chemin supporté demande de documenter {0}/ à cet emplacement',
}
