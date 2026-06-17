/* Génération du rapport TFE Vellucast — docx-js. Exécuter avec NODE_PATH global. (build) */
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  ImageRun, Header, Footer, AlignmentType, LevelFormat, TableOfContents,
  HeadingLevel, BorderStyle, WidthType, ShadingType, PageNumber, PageBreak, TabStopType, TabStopPosition,
} = require("docx");

const IMG = "/sessions/zealous-compassionate-lovelace/mnt/outputs/report/img";
const OUT = "/sessions/zealous-compassionate-lovelace/mnt/Projet TFE - Copie (2)/Rapport_TFE_Vellucast_complet.docx";
const CW = 9360; // content width DXA (US Letter, 1" margins)

// ---- PNG size ----
function pngSize(p){ const b=fs.readFileSync(p); return { w:b.readUInt32BE(16), h:b.readUInt32BE(20) }; }
function imgFit(p, maxW=600, maxH=760){ const {w,h}=pngSize(p); const s=Math.min(maxW/w, maxH/h, 1); return { width:Math.round(w*s), height:Math.round(h*s) }; }

// ---- helpers ----
const FONT="Arial";
const C_INK="1E293B", C_ACC="4338CA", C_MUT="475569";
let figN=0, tblN=0;
function H1(t){ return new Paragraph({ heading:HeadingLevel.HEADING_1, pageBreakBefore:true, children:[new TextRun(t)] }); }
function H2(t){ return new Paragraph({ heading:HeadingLevel.HEADING_2, children:[new TextRun(t)] }); }
function H3(t){ return new Paragraph({ heading:HeadingLevel.HEADING_3, children:[new TextRun(t)] }); }
function P(t,opt={}){ return new Paragraph({ alignment:AlignmentType.JUSTIFIED, spacing:{after:160, line:340}, children:[new TextRun({text:t, size:22})], ...opt }); }
function runs(arr){ return new Paragraph({ alignment:AlignmentType.JUSTIFIED, spacing:{after:160, line:340}, children:arr }); }
function BULL(items){ return items.map(it=> new Paragraph({ numbering:{reference:"bul", level:0}, spacing:{after:80, line:320}, children:[ typeof it==="string"? new TextRun({text:it,size:22}) : it ] })); }
function NUM(items){ return items.map(it=> new Paragraph({ numbering:{reference:"num", level:0}, spacing:{after:80, line:320}, children:[new TextRun({text:it,size:22})] })); }
function FIG(file, caption, maxW=600, maxH=760){
  figN++; const fit=imgFit(`${IMG}/${file}`,maxW,maxH);
  return [
    new Paragraph({ alignment:AlignmentType.CENTER, spacing:{before:120,after:40}, children:[ new ImageRun({ type:"png", data:fs.readFileSync(`${IMG}/${file}`), transformation:fit, altText:{title:caption,description:caption,name:file} }) ] }),
    new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:200}, children:[ new TextRun({text:`Figure ${figN} — ${caption}`, italics:true, size:18, color:C_MUT}) ] }),
  ];
}
function cell(text,{w,head=false,bold=false,fill}={}){
  const border={style:BorderStyle.SINGLE,size:1,color:"CBD5E1"};
  return new TableCell({
    width:{size:w,type:WidthType.DXA},
    borders:{top:border,bottom:border,left:border,right:border},
    shading:{fill: fill || (head?"312E81":"FFFFFF"), type:ShadingType.CLEAR},
    margins:{top:60,bottom:60,left:110,right:110},
    children:(Array.isArray(text)?text:[text]).map(t=> new Paragraph({children:[new TextRun({text:String(t), bold:head||bold, size:19, color:head?"FFFFFF":C_INK})]}))
  });
}
function TBL(headers, rows, widths, caption){
  tblN++;
  const t = new Table({
    width:{size:CW,type:WidthType.DXA}, columnWidths:widths,
    rows:[
      new TableRow({tableHeader:true, children:headers.map((h,i)=>cell(h,{w:widths[i],head:true}))}),
      ...rows.map(r=> new TableRow({children:r.map((c,i)=>cell(c,{w:widths[i]}))}))
    ]
  });
  const cap = new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:200, before:40}, children:[new TextRun({text:`Tableau ${tblN} — ${caption}`, italics:true, size:18, color:C_MUT})]});
  return [t, cap];
}
function CODE(lines, title){
  const out=[];
  if(title) out.push(new Paragraph({spacing:{before:120,after:40},children:[new TextRun({text:title,italics:true,size:18,color:C_MUT})]}));
  out.push(new Paragraph({
    spacing:{after:160}, shading:{fill:"0F172A",type:ShadingType.CLEAR},
    border:{top:{style:BorderStyle.SINGLE,size:2,color:"334155"},left:{style:BorderStyle.SINGLE,size:2,color:"334155"},bottom:{style:BorderStyle.SINGLE,size:2,color:"334155"},right:{style:BorderStyle.SINGLE,size:2,color:"334155"}},
    children: lines.flatMap((l,i)=>[ ...(i?[new TextRun({break:1})]:[]), new TextRun({text:l||" ",font:"Consolas",size:16,color:"E2E8F0"}) ])
  }));
  return out;
}

const children=[];
const push=(...x)=>x.forEach(e=>Array.isArray(e)?children.push(...e):children.push(e));

// ============== PAGE DE GARDE ==============
push(new Paragraph({ spacing:{before:1200,after:120}, alignment:AlignmentType.CENTER, children:[new TextRun({text:"RAPPORT DE TRAVAIL DE FIN D'ÉTUDES", bold:true, size:30, color:C_ACC})] }));
push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:600}, children:[new TextRun({text:"Année académique 2025 – 2026", size:22, color:C_MUT})] }));
push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:80}, children:[new TextRun({text:"VELLUCAST", bold:true, size:64, color:C_INK})] }));
push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:60}, children:[new TextRun({text:"Conception et réalisation d'une plateforme de streaming", size:26, color:C_INK})] }));
push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:500}, children:[new TextRun({text:"multimédia auto-hébergée et intelligente", size:26, color:C_INK})] }));
push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:700}, children:[new TextRun({text:"Une alternative modulaire et sécurisée aux solutions propriétaires,\navec gestion avancée du transcodage et partage temporaire maîtrisé.", italics:true, size:22, color:C_MUT})] }));
push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:40}, children:[new TextRun({text:"Présenté par : Julien HOORENS", bold:true, size:24})] }));
push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:40}, children:[new TextRun({text:"Bachelier en informatique — orientation Développement d'applications", size:22})] }));
push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:40}, children:[new TextRun({text:"Enseignement supérieur économique de type court", size:20, color:C_MUT})] }));
push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:{after:40}, children:[new TextRun({text:"Superviseur : [Nom du superviseur]", size:22})] }));
push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:{before:200}, children:[new TextRun({text:"Dépôt GitHub : github.com/ElFifux540/vellucast", size:20, color:C_ACC})] }));

// ============== CONFIDENTIALITÉ + REMERCIEMENTS ==============
push(new Paragraph({ pageBreakBefore:true, heading:HeadingLevel.HEADING_1, children:[new TextRun("Clause de confidentialité")] }));
push(P("« Le présent travail de fin d'études est soumis à une clause de confidentialité. Son contenu ne peut être communiqué à des tiers sans autorisation préalable (voir annexe). »"));
push(P("« L'étudiant autorise la diffusion et le partage public de ce travail à des fins pédagogiques pour les futurs étudiants. »"));
push(H1("Remerciements"));
push(P("Je tiens tout d'abord à exprimer ma profonde gratitude à mon superviseur pour son accompagnement précieux, sa disponibilité et ses conseils avisés qui ont jalonné la conception de cette plateforme de streaming multimédia. Ses orientations techniques m'ont permis de mener à bien ce projet ambitieux avec rigueur et méthode."));
push(P("Je remercie également l'ensemble du corps professoral de ma section pour les compétences transmises tout au long de mon cursus, ainsi que les utilisateurs testeurs qui ont accepté de me faire part de leurs retours d'expérience et de leurs frustrations vis-à-vis des solutions existantes."));
push(P("Enfin, je remercie chaleureusement mes proches pour leur soutien indéfectible et leur patience durant la réalisation de ce travail. Leur présence à mes côtés a été une source de motivation essentielle pour transformer cette vision technique en une solution fonctionnelle et aboutie."));

// ============== RÉSUMÉ ==============
push(H1("Résumé"));
push(P("Ce travail de fin d'études présente la conception et la réalisation de Vellucast, une plateforme web de streaming multimédia auto-hébergée destinée aux utilisateurs avancés souhaitant reprendre le contrôle de leur médiathèque personnelle. Le projet répond à une problématique concrète : les solutions de streaming existantes, qu'elles soient propriétaires ou libres, imposent des limites techniques et économiques (transcodage matériel payant, dépendance à des serveurs tiers, partage rigide) qui freinent les « power users »."));
push(P("Vellucast s'appuie sur une architecture client-serveur asynchrone — un backend Python/FastAPI, une base de données SQLite et une interface Vue 3 — et exploite FFmpeg pour le traitement vidéo. Trois apports différenciants structurent le travail : un transcodage intelligent (planifié en heures creuses et à la volée en HLS lorsque le navigateur ne sait pas lire le codec source), un système de partage temporaire multi-contenus sécurisé par jeton scopé, et une indexation résiliente reposant sur des identifiants immuables insensibles aux déplacements de fichiers."));
push(P("Le rapport détaille l'analyse fonctionnelle (UML), l'analyse des données (méthode Merise et diagramme de classes), l'analyse des traitements (diagrammes de séquence, d'activité et d'états), les choix de conception, la réalisation, la stratégie de tests et le déploiement. Il se conclut par une évaluation critique du travail et par les perspectives d'évolution."));
push(runs([new TextRun({text:"Mots-clés : ", bold:true, size:22}), new TextRun({text:"streaming, auto-hébergement, transcodage, HLS, FFmpeg, FastAPI, Vue.js, SQLite, partage sécurisé, UML, Merise.", size:22, italics:true})]));

// ============== TOC ==============
push(new Paragraph({ pageBreakBefore:true, heading:HeadingLevel.HEADING_1, children:[new TextRun("Table des matières")] }));
push(new TableOfContents("Table des matières", { hyperlink:true, headingStyleRange:"1-3" }));

// ============== 1. INTRODUCTION ==============
push(H1("1. Introduction"));
push(H2("1.1 Contexte général"));
push(P("Depuis plusieurs années, les plateformes de streaming multimédia se sont imposées comme une solution incontournable pour accéder à des contenus audiovisuels de manière fluide et centralisée. Dans le même temps, le mouvement de l'auto-hébergement (self-hosting) connaît un essor important : de plus en plus d'utilisateurs disposent de leur propre matériel — serveur personnel, NAS, mini-PC de type Intel NUC — et souhaitent héberger eux-mêmes leurs services pour des raisons de coût, de contrôle et de respect de la vie privée."));
push(P("Ce travail de fin d'études s'inscrit dans le cadre de l'obtention du diplôme de Bachelier en informatique, orientation développement d'applications. Il vise à concevoir et développer un système complet de gestion et de diffusion de médias personnels, répondant à une problématique croissante dans le domaine du divertissement numérique et de l'auto-hébergement."));
push(H2("1.2 Problématique"));
push(P("Les solutions existantes présentent des limitations techniques et un modèle économique qui freinent les utilisateurs avancés souhaitant une expérience réellement personnalisée. Le transcodage matériel est fréquemment réservé à des abonnements payants ; l'authentification dépend parfois de serveurs tiers ; le partage de contenu à un proche reste rigide ou inexistant nativement ; et le renommage ou le déplacement d'un fichier sur le disque casse souvent l'indexation. La problématique centrale de ce travail est donc la suivante : "));
push(runs([new TextRun({text:"comment concevoir une plateforme de streaming auto-hébergée, modulaire et sécurisée, qui combine performance et autonomie, tout en offrant des fonctionnalités de partage et de transcodage que les solutions du marché ne proposent pas nativement ?", italics:true, bold:true, size:22})]));
push(H2("1.3 Objectifs"));
push(P("L'objectif principal est de développer une application web auto-hébergée permettant d'organiser une bibliothèque multimédia, de la diffuser en direct dans un navigateur, de la partager de façon contrôlée et d'automatiser les tâches de maintenance. Les objectifs spécifiques sont :"));
push(...BULL([
 "offrir une indexation résiliente, insensible aux déplacements et renommages physiques des fichiers ;",
 "proposer un transcodage intelligent : planifié durant les heures creuses, et à la volée lorsque le codec source n'est pas lisible par le navigateur ;",
 "permettre un partage temporaire et sécurisé de plusieurs contenus à des invités, sans création de compte ;",
 "intégrer une source de métadonnées externe (Overseerr / TMDb) pour enrichir l'expérience ;",
 "garantir un socle de sécurité solide (hachage robuste des mots de passe, jetons signés, limitation de débit)."]));
push(P("Sur le plan de l'apprentissage personnel, ce TFE a pour objectif de me confronter à l'architecture asynchrone, à l'administration d'environnements Linux et à la manipulation de flux vidéo, consolidant ainsi les acquis de ma formation."));
push(H2("1.4 Structure du document"));
push(P("Le document s'organise comme suit. Le chapitre 2 présente le contexte, l'étude de l'existant, les concepts techniques mobilisés et les aspects légaux. Le chapitre 3 formalise le cahier des charges. Le chapitre 4 développe l'analyse (cas d'utilisation UML, modèle de données Merise, diagrammes de traitements). Le chapitre 5 expose la conception et les choix techniques. Le chapitre 6 décrit la réalisation. Le chapitre 7 traite des tests, le chapitre 8 du déploiement et de l'exploitation, le chapitre 9 de la gestion de projet. Les chapitres 10 et 11 proposent une évaluation critique et une conclusion. Suivent la bibliographie, le glossaire et les annexes."));

// ============== 2. CONTEXTE ==============
push(H1("2. Contexte et état de l'art"));
push(H2("2.1 Le client : un public cible de « power users »"));
push(P("Dans le cadre de ce projet, le « client » n'est pas une entité commerciale unique, mais se définit par une communauté d'utilisateurs exigeants et avancés. Ce public recherche une expérience auto-hébergée et souhaite s'affranchir des contraintes imposées par les logiciels propriétaires. Ce profil dispose généralement de son propre matériel et souhaite optimiser la consommation de ses ressources tout en gardant un contrôle total sur la qualité de diffusion et l'organisation de ses fichiers."));
push(H2("2.2 La demande initiale"));
push(P("La demande fondamentale consiste en la création d'une alternative libre, flexible et sécurisée aux plateformes de streaming centralisées. Le système doit être modulaire et extensible, capable de combiner performance et autonomie. Les besoins critiques identifiés sont une gestion fine du transcodage vidéo pour optimiser la qualité sans saturer le serveur, une indépendance vis-à-vis des services tiers pour la lecture du contenu, et une automatisation poussée de la gestion des médias (renommage, suivi des sorties)."));
push(H2("2.3 Étude de l'existant"));
push(P("L'étude comparative des solutions de gestion multimédia auto-hébergées révèle plusieurs producteurs dominants. Bien que matures, ces outils présentent des caractéristiques contrastées qui justifient la création d'une alternative. Le tableau suivant synthétise cette analyse."));
push(...TBL(
 ["Solution","Points forts","Points faibles"],
 [
  ["Plex","Interface aboutie, large écosystème d'applications clientes (Smart TV, consoles), excellente gestion des métadonnées.","Modèle commercial fermé (transcodage matériel payant), dépendance d'authentification envers des serveurs tiers, renommage rigide."],
  ["Jellyfin","100 % open-source et gratuit, transcodage matériel inclus, indépendance totale et respect de la vie privée.","Interface d'administration moins intuitive, écosystème d'applications moins stable, peu de flexibilité pour le partage externe."],
  ["Emby","Bon compromis technique, gestion fine du contrôle parental et des autorisations d'utilisateurs.","Passage d'un modèle open-source à un modèle propriétaire payant aux licences restrictives."],
  ["Vellucast","Partage temporaire multi-contenus natif, transcodage planifié et à la volée, indexation résiliente, intégration Overseerr.","Projet jeune (MVP), écosystème client limité au navigateur, pas encore d'accélération matérielle."],
 ],
 [1600,3880,3880],
 "Étude comparative des solutions de streaming auto-hébergées"));
push(P("Face à ces concurrents, Vellucast se distingue par quatre apports : la génération de liens de visionnage invités (avec date d'expiration, limite d'utilisation et code PIN) de manière native et sécurisée ; un transcodage asynchrone et planifié permettant d'optimiser les fichiers durant les heures creuses ; une résilience de la base de données grâce à des identifiants uniques rendant le système insensible aux déplacements physiques de fichiers ; et une expérience centralisée via l'intégration de l'API Overseerr."));
push(H2("2.4 Concepts techniques mobilisés"));
push(H3("2.4.1 Conteneurs et codecs"));
push(P("Un fichier vidéo est un conteneur (MP4, MKV…) encapsulant un ou plusieurs flux encodés par des codecs (H.264/AVC, H.265/HEVC pour la vidéo ; AAC, AC3 pour l'audio). Les navigateurs web ne savent lire nativement qu'un sous-ensemble restreint de combinaisons — typiquement du H.264/AAC dans un conteneur MP4. Une grande partie d'une médiathèque réelle (MKV en H.265, pistes AC3) n'est donc pas directement lisible, ce qui rend le transcodage indispensable."));
push(H3("2.4.2 Transcodage et streaming adaptatif (HLS)"));
push(P("Le transcodage consiste à ré-encoder un flux d'un format vers un autre. Il peut être effectué en amont (le fichier est converti une fois pour toutes) ou à la volée (durant la lecture). Le HLS (HTTP Live Streaming) découpe le flux en petits segments (.ts) décrits par une playlist (.m3u8) que le client télécharge progressivement. Cette approche, fondée sur HTTP, traverse aisément les pare-feu et permet une lecture fluide. Vellucast combine les deux stratégies : optimisation planifiée des fichiers et transcodage HLS à la volée en cas d'incompatibilité."));
push(H3("2.4.3 Requêtes partielles HTTP (Range)"));
push(P("Pour la lecture directe, le serveur répond aux requêtes HTTP Range (code 206 Partial Content) : le lecteur ne demande que la portion de fichier nécessaire, ce qui autorise le déplacement instantané dans la vidéo (seek) et une consommation mémoire bornée côté serveur grâce à une lecture par morceaux (chunks)."));
push(H3("2.4.4 Architecture web découplée et API REST"));
push(P("Vellucast adopte une architecture web découplée : le frontend (Vue 3) et le backend (FastAPI) communiquent exclusivement par une API REST échangeant du JSON. Ce découplage présente plusieurs avantages : il permet de faire évoluer l'interface et le serveur indépendamment, d'envisager à terme des clients alternatifs (application mobile native) consommant la même API, et de tester chaque couche séparément. Les endpoints suivent les conventions REST (verbes HTTP, codes de statut signifiants) et l'authentification est portée par un en-tête Authorization Bearer, ou par un paramètre de requête pour les balises vidéo qui ne peuvent pas porter d'en-tête."));
push(H3("2.4.5 Programmation asynchrone"));
push(P("Le streaming et le transcodage sont des opérations fortement liées aux entrées/sorties. Un modèle synchrone bloquerait un fil d'exécution pendant la lecture d'un fichier ou l'attente d'un sous-processus, limitant fortement le nombre d'utilisateurs simultanés. Le modèle asynchrone (async/await) de Python, exploité par FastAPI et le driver aiosqlite, permet au serveur de traiter de nombreuses requêtes concurrentes sur une seule boucle d'événements, en libérant le fil pendant les attentes d'E/S. Les opérations bloquantes (lecture de fichiers, sous-processus FFmpeg) sont déportées dans des threads dédiés afin de ne jamais figer cette boucle."));
push(H2("2.5 Aspects légaux et conformité réglementaire"));
push(P("S'agissant d'une plateforme gérant la diffusion de flux multimédias et l'hébergement de données, la viabilité du projet repose sur la prise en compte stricte de plusieurs cadres légaux, particulièrement en matière de propriété intellectuelle."));
push(H3("2.5.1 Droit d'auteur, copie privée et « Bring Your Own Content »"));
push(P("L'application développée est, par essence, une coquille vide conçue comme un outil technique neutre reposant sur le principe du Bring Your Own Content (BYOC) : elle ne fournit, n'héberge et n'indexe par défaut aucun contenu protégé. L'entière responsabilité de la licéité des fichiers source incombe à l'administrateur. L'exception de copie privée permet de stocker des œuvres provenant d'une source licite pour un usage strictement personnel ; le cercle de famille restreint la représentation à un cadre familial ou amical proche (Code de droit économique en Belgique)."));
push(P("C'est précisément pour respecter cette exigence que la fonctionnalité de partage par lien temporaire a été bridée techniquement. En imposant des quotas d'utilisation stricts, des dates d'expiration courtes et une protection facultative par code PIN, l'architecture empêche activement la diffusion massive, évitant toute assimilation du service à une communication au public non autorisée."));
push(H3("2.5.2 Droit à l'image, licences d'API et métadonnées"));
push(P("Pour enrichir l'expérience, l'application interroge dynamiquement des API publiques (TMDb, TVmaze) via l'intégration d'Overseerr. Dans le cadre de ce projet à but non commercial et éducatif, l'exploitation de ces API est couverte par leurs licences gratuites pour développeurs, sous réserve de respecter les limites de requêtes (rate limiting) et d'inclure les attributions requises pour créditer la source des affiches et des synopsis."));
push(H3("2.5.3 Données personnelles (RGPD)"));
push(P("Les seules données personnelles traitées sont les identifiants des comptes et des journaux techniques d'usage (adresse IP, user-agent, horodatage) destinés à l'audit de sécurité. Ces données restent sur le serveur de l'utilisateur, ne sont jamais transmises à un tiers et peuvent être purgées. Les mots de passe ne sont jamais stockés en clair (hachage PBKDF2)."));

// ============== 3. CAHIER DES CHARGES ==============
push(H1("3. Cahier des charges"));
push(H2("3.1 Méthodologie d'élaboration"));
push(P("L'élaboration du cahier des charges s'est déroulée selon une approche d'analyse agile, itérative et incrémentale, structurée autour de plusieurs phases d'échanges visant à cerner les besoins réels de l'environnement d'exploitation. La première rencontre a permis de définir le périmètre général. Des entretiens réguliers menés auprès du public cible ont mis en lumière les frustrations majeures vécues sur les plateformes existantes, ainsi que les usages quotidiens, la fréquence de partage de fichiers vers des tiers et les contraintes de bande passante subies lors des visionnages simultanés."));
push(H2("3.2 Besoins fonctionnels"));
push(P("Les besoins fonctionnels ont été priorisés selon la méthode MoSCoW (Must, Should, Could, Won't) afin de cadrer le périmètre de la première version."));
push(...TBL(
 ["Réf.","Besoin fonctionnel","Priorité"],
 [
  ["BF-01","Authentification par compte (administrateur / utilisateur)","Must"],
  ["BF-02","Indexation des médias par identifiant unique immuable","Must"],
  ["BF-03","Streaming direct dans le navigateur (HTTP Range)","Must"],
  ["BF-04","Transcodage à la volée (HLS) si codec incompatible","Must"],
  ["BF-05","Génération de liens de partage temporaires (expiration, quota, PIN)","Must"],
  ["BF-06","Accès invité au(x) contenu(s) partagé(s) sans compte","Must"],
  ["BF-07","Optimisation planifiée des fichiers (heures creuses)","Should"],
  ["BF-08","Recherche dans la bibliothèque (classement par pertinence)","Should"],
  ["BF-09","Association de métadonnées via Overseerr (affiche, synopsis)","Should"],
  ["BF-10","Partage portant sur plusieurs contenus à la fois","Should"],
  ["BF-11","Gestion des séries (saisons / épisodes)","Should"],
  ["BF-12","Journal d'audit des actions sensibles","Could"],
  ["BF-13","Thème sombre et préférences d'affichage par utilisateur","Could"],
  ["BF-14","Applications clientes natives (mobile / TV)","Won't (v1)"],
 ],
 [1100,6660,1600],
 "Besoins fonctionnels priorisés (MoSCoW)"));
push(H2("3.3 Besoins non-fonctionnels"));
push(...TBL(
 ["Catégorie","Exigence"],
 [
  ["Performance","E/S non bloquantes ; lecture par chunks ; transcodage en sous-processus pour ne pas bloquer la boucle d'événements."],
  ["Sécurité","Hachage PBKDF2, jetons HMAC signés, limitation de débit, jetons invités scopés, protection anti-traversée de répertoire, en-têtes HTTP de sécurité."],
  ["Portabilité","Base SQLite (fichier unique), déploiement par clonage Git et environnement virtuel Python."],
  ["Ergonomie","Interface réactive et responsive, inspirée des standards (Plex), prise en main immédiate pour l'invité."],
  ["Résilience","Indexation insensible aux déplacements/renommages ; migration de schéma sans perte de données."],
  ["Maintenabilité","Architecture modulaire (un module par responsabilité), journalisation, documentation."],
 ],
 [2200,7160],
 "Besoins non-fonctionnels"));
push(H2("3.4 Les acteurs de l'environnement"));
push(...TBL(
 ["Acteur","Rôle"],
 [
  ["Administrateur système","Déploiement (Git), configuration des dossiers et des presets de transcodage, gestion des contenus, des utilisateurs et des partages."],
  ["Utilisateur final","Consomme le contenu, parcourt et recherche la bibliothèque, gère son mot de passe."],
  ["Invité","Accède temporairement à un ou plusieurs contenus via un lien, sans compte."],
  ["Overseerr (service tiers)","Source de vérité pour les métadonnées (TMDb / TVmaze)."],
  ["FFmpeg (outil système)","Moteur sous-jacent exécutant les tâches de traitement vidéo."],
 ],
 [2600,6760],
 "Acteurs de l'environnement"));
push(H2("3.5 Lots d'informations"));
push(P("L'analyse des flux de données a permis d'isoler plusieurs catégories de lots d'informations : les fichiers vidéo bruts d'origine (MKV, MP4), à conserver sans altération destructrice ; les anciens index texte et arborescences rigides, à remplacer par une indexation dynamique en base relationnelle ; et les nouveaux lots produits par le système : jetons cryptographiques de partage, données d'analyse d'usage (IP, navigateurs), playbacks partiels et métadonnées enrichies au format JSON provenant d'API tierces."));
push(H2("3.6 Périmètre de la première version et perspectives"));
push(P("La première version livre l'ensemble des besoins « Must » et la majorité des « Should ». Les perspectives d'évolution comprennent le support de l'accélération matérielle GPU (NVIDIA NVENC / Intel QuickSync), les applications clientes natives, la gestion des métadonnées locales (fichiers NFO) et des pistes audio/sous-titres multiples, ainsi qu'une conteneurisation Docker Compose unifiée."));

// ============== 4. ANALYSE ==============
push(H1("4. Analyse"));
push(P("Ce chapitre formalise l'analyse du système selon trois axes complémentaires : l'analyse fonctionnelle (ce que le système doit faire, via les cas d'utilisation UML), l'analyse des données (la structure de l'information, via la méthode Merise et un diagramme de classes UML) et l'analyse des traitements (la dynamique, via des diagrammes de séquence, d'activité et d'états)."));
push(H2("4.1 Analyse fonctionnelle"));
push(H3("4.1.1 Diagramme de cas d'utilisation"));
push(P("Le diagramme de cas d'utilisation ci-dessous recense les interactions entre les acteurs et le système. On distingue trois acteurs humains (administrateur, utilisateur, invité) et deux acteurs externes (Overseerr et FFmpeg). Les relations « include » expriment des inclusions obligatoires (visionner inclut le transcodage éventuel ; accéder par lien inclut l'authentification invité), tandis que la relation « extend » modélise une extension optionnelle (l'ajout d'un média peut être prolongé par une association de métadonnées)."));
push(...FIG("uc_usecases.png","Diagramme de cas d'utilisation de Vellucast",420,720));
push(H3("4.1.2 Description textuelle des cas d'utilisation principaux"));
push(P("Conformément aux conventions, chaque cas d'utilisation critique est décrit par une fiche détaillant ses acteurs, préconditions, scénario nominal et scénarios alternatifs. Deux fiches représentatives sont présentées ci-dessous."));
push(...TBL(
 ["Rubrique","Cas d'utilisation « Visionner un média »"],
 [
  ["Acteur principal","Utilisateur (ou invité)"],
  ["Préconditions","L'acteur est authentifié ; le contenu existe et son fichier est présent sur le disque."],
  ["Scénario nominal","1. L'acteur sélectionne un contenu. 2. Le client interroge l'endpoint d'information de lecture. 3. Le serveur sonde les codecs et renvoie le mode recommandé. 4a. Si compatible : lecture directe en HTTP Range. 4b. Sinon : démarrage d'une session HLS et lecture via le lecteur Plyr."],
  ["Scénarios alternatifs","3a. ffprobe indisponible → repli en lecture directe. 4b-1. FFmpeg absent → message d'erreur explicite."],
  ["Postconditions","Le flux vidéo est diffusé dans le navigateur de l'acteur."],
 ],
 [1900,7460],
 "Fiche descriptive — Visionner un média"));
push(...TBL(
 ["Rubrique","Cas d'utilisation « Accéder par lien temporaire »"],
 [
  ["Acteur principal","Invité"],
  ["Préconditions","Un lien de partage valide (non expiré, quota non atteint) a été généré par l'administrateur."],
  ["Scénario nominal","1. L'invité ouvre le lien et saisit le code PIN si requis. 2. Le serveur valide le lien et consomme une utilisation. 3. Le serveur émet un jeton invité scopé portant la liste des contenus autorisés. 4. L'invité visionne le(s) contenu(s) partagé(s)."],
  ["Scénarios alternatifs","2a. Lien expiré / quota atteint / PIN erroné → accès refusé avec message explicite."],
  ["Postconditions","Une trace d'usage (IP, user-agent, horodatage) est enregistrée."],
 ],
 [1900,7460],
 "Fiche descriptive — Accéder par lien temporaire"));
push(...TBL(
 ["Rubrique","Cas d'utilisation « S'authentifier »"],
 [
  ["Acteur principal","Utilisateur, Administrateur"],
  ["Préconditions","L'acteur possède un compte actif."],
  ["Scénario nominal","1. L'acteur saisit son nom d'utilisateur et son mot de passe. 2. Le système applique une limitation de débit sur l'adresse IP. 3. Le système vérifie l'empreinte du mot de passe (PBKDF2). 4. Un jeton signé à durée de vie limitée est émis et la session est restaurée."],
  ["Scénarios alternatifs","3a. Empreinte d'un ancien algorithme détectée → vérification puis ré-encodage transparent (migration « lazy »). 3b. Identifiants invalides → message d'erreur, l'acteur reste sur l'écran de connexion. 2a. Trop de tentatives → réponse 429 (temporisation)."],
  ["Postconditions","L'acteur est connecté ; le jeton est conservé côté client pour la persistance de session."],
 ],
 [1900,7460],
 "Fiche descriptive — S'authentifier"));
push(...TBL(
 ["Rubrique","Cas d'utilisation « Créer un lien de partage »"],
 [
  ["Acteur principal","Administrateur"],
  ["Préconditions","L'administrateur est authentifié ; au moins un contenu est indexé."],
  ["Scénario nominal","1. L'administrateur coche un ou plusieurs contenus. 2. Il définit une durée d'expiration, un quota d'utilisations et, facultativement, un code PIN. 3. Le système génère un jeton aléatoire, persiste le lien et ses contenus, et hache le code PIN. 4. Le lien est restitué pour diffusion."],
  ["Scénarios alternatifs","1a. Aucun contenu coché → création refusée avec message. 3a. Contenu introuvable → erreur explicite."],
  ["Postconditions","Un lien valide est créé ; l'action est tracée dans le journal d'audit."],
 ],
 [1900,7460],
 "Fiche descriptive — Créer un lien de partage"));
push(...TBL(
 ["Rubrique","Cas d'utilisation « Ajouter un média »"],
 [
  ["Acteur principal","Administrateur"],
  ["Préconditions","L'administrateur est authentifié ; un dossier média est configuré."],
  ["Scénario nominal","1. L'administrateur sélectionne un fichier vidéo (film ou épisode). 2. Le système écrit le fichier par morceaux dans l'arborescence appropriée. 3. Un identifiant unique immuable est généré et le contenu est inséré en base. 4. (Extension) L'administrateur associe des métadonnées via Overseerr."],
  ["Scénarios alternatifs","2a. Format non supporté → conversion d'extension ou refus. 4a. Overseerr non configuré → ajout sans enrichissement."],
  ["Postconditions","Le média est indexé et visible dans la bibliothèque."],
 ],
 [1900,7460],
 "Fiche descriptive — Ajouter un média"));
push(H2("4.2 Analyse des données"));
push(P("L'analyse des données est conduite selon la méthode Merise (modèle conceptuel puis logique) afin d'établir une modélisation rigoureuse, complétée par un diagramme de classes UML reflétant l'orientation objet de l'implémentation."));
push(H3("4.2.1 Règles de gestion"));
push(...NUM([
 "Un utilisateur possède un rôle unique (administrateur ou utilisateur).",
 "Un contenu est identifié par un identifiant unique immuable, indépendant de son chemin physique.",
 "Un lien de partage est créé par un et un seul utilisateur ; un utilisateur peut créer plusieurs liens.",
 "Un lien de partage concerne un ou plusieurs contenus ; un contenu peut figurer dans plusieurs liens.",
 "Un lien de partage donne lieu à zéro ou plusieurs usages, chacun horodaté.",
 "Un lien possède éventuellement une date d'expiration, un quota d'utilisations et un code d'accès haché.",
 "Toute action sensible est tracée dans un journal d'audit.",
]));
push(H3("4.2.2 Modèle conceptuel des données (MCD)"));
push(P("Le MCD ci-dessous représente les entités, leurs propriétés et les associations qui les relient, avec leurs cardinalités. On note notamment l'association « concerne » de cardinalité (1,n)–(0,n) entre LIEN_PARTAGE et CONTENU, qui traduit le partage multi-contenus."));
push(...FIG("mcd.png","Modèle conceptuel des données (Merise)",640,520));
push(H3("4.2.3 Dictionnaire de données"));
push(P("Le dictionnaire de données recense les principales propriétés manipulées par le système, leur type et leurs contraintes."));
push(...TBL(
 ["Donnée","Type","Description / contrainte"],
 [
  ["id_utilisateur","Entier","Identifiant technique, clé primaire, auto-incrémenté."],
  ["username","Texte","Nom d'utilisateur, unique, non nul."],
  ["password_hash","Texte","Empreinte PBKDF2 du mot de passe."],
  ["role","Texte","Valeur dans {admin, user}."],
  ["id_contenu","Texte","Identifiant unique immuable du média (clé primaire)."],
  ["titre","Texte","Titre affiché, non nul."],
  ["chemin_media","Texte","Chemin absolu du fichier (sous MEDIA_FOLDER)."],
  ["poster_url / backdrop_url","Texte","URL de l'affiche / bannière (métadonnées)."],
  ["tmdb_id","Texte","Identifiant TMDb après association (nullable)."],
  ["token","Texte","Jeton aléatoire du lien de partage, unique."],
  ["expire_le","Date/heure","Date d'expiration du lien (nullable)."],
  ["max_utilisations","Entier","Quota d'usages (nullable = illimité)."],
  ["code_acces_hash","Texte","Empreinte du code PIN (nullable)."],
  ["utilise_le","Date/heure","Horodatage d'un usage de lien."],
 ],
 [2600,1500,5260],
 "Dictionnaire de données (extrait)"));
push(H3("4.2.4 Modèle logique des données (MLD)"));
push(P("Le passage du MCD au MLD applique les règles classiques : chaque entité devient une table, et l'association porteuse de cardinalités multiples des deux côtés (« concerne ») se traduit par une table de jointure share_link_contents. La clé étrangère content_id historique est conservée sur share_links pour la compatibilité ascendante des liens créés avant l'évolution multi-contenus."));
push(...FIG("mld.png","Modèle logique des données (schéma relationnel)",640,440));
push(H3("4.2.5 Diagramme de classes UML"));
push(P("Le diagramme de classes traduit la même information sous un angle orienté objet, en ajoutant les opérations (méthodes) portées par chaque classe métier."));
push(...FIG("class_diagram.png","Diagramme de classes UML",600,720));
push(H2("4.3 Analyse des traitements"));
push(P("L'analyse dynamique s'appuie sur des diagrammes de séquence (interactions temporelles entre objets), un diagramme d'activité (flux d'un traitement automatisé) et un diagramme d'états (cycle de vie d'un objet)."));
push(H3("4.3.1 Authentification"));
push(P("La séquence d'authentification illustre la limitation de débit, la vérification PBKDF2 et la migration « lazy » des anciens hachages, ainsi que l'émission d'un jeton signé."));
push(...FIG("seq_login.png","Diagramme de séquence — Authentification",540,640));
push(H3("4.3.2 Visionnage et décision de transcodage"));
push(P("Cette séquence est au cœur du système : le serveur sonde le média et choisit entre lecture directe et transcodage HLS, puis le lecteur consomme la playlist et les segments."));
push(...FIG("seq_stream.png","Diagramme de séquence — Visionnage (décision HLS)",540,680));
push(H3("4.3.3 Partage temporaire multi-contenus"));
push(P("La séquence du partage couvre la création du lien par l'administrateur, son utilisation par l'invité (validation, consommation d'un usage, émission d'un jeton invité scopé) et l'autorisation au niveau du flux."));
push(...FIG("seq_share.png","Diagramme de séquence — Partage temporaire multi-contenus",560,760));
push(H3("4.3.4 Ajout d'un média et association de métadonnées"));
push(...FIG("seq_upload.png","Diagramme de séquence — Upload et association Overseerr",560,760));
push(H3("4.3.5 Diagramme d'activité : worker d'optimisation"));
push(P("Le worker d'optimisation s'exécute périodiquement et n'agit que dans la plage horaire configurée, en ignorant les fichiers déjà optimisés ou en cours de lecture."));
push(...FIG("act_optimizer.png","Diagramme d'activité — Worker d'optimisation planifiée",420,720));
push(H3("4.3.6 Diagramme d'états : cycle de vie d'un lien de partage"));
push(...FIG("state_share.png","Diagramme d'états — Lien de partage",640,360));
push(H2("4.4 Architecture logique"));
push(P("Le diagramme de composants présente l'organisation logique de l'application : les composants du frontend, les modules du backend et les services/systèmes externes."));
push(...FIG("comp_architecture.png","Diagramme de composants — Architecture logique",600,640));

// ============== 5. CONCEPTION ==============
push(H1("5. Conception et choix techniques"));
push(H2("5.1 Choix des outils"));
push(...TBL(
 ["Technologie","Rôle","Justification"],
 [
  ["Python + FastAPI","Backend / API","Gestion native de l'asynchronisme (async/await), indispensable pour traiter les flux de streaming et les opérations d'E/S non bloquantes."],
  ["SQLite + aiosqlite","Base de données","Empreinte légère (fichier unique portable) et driver asynchrone évitant les blocages de la boucle d'événements."],
  ["Vue 3 + Vite","Frontend","Environnement réactif idéal pour des tableaux de bord et des vues mises à jour en temps réel ; outillage de build rapide."],
  ["FFmpeg / ffprobe","Traitement vidéo","Standard de fait pour le transcodage et l'analyse de flux ; piloté en sous-processus."],
  ["hls.js + Plyr","Lecteur web","Lecture HLS dans les navigateurs sans support natif ; interface de lecture moderne."],
  ["Nginx","Reverse proxy","Redirection du trafic externe vers l'API locale et service des fichiers statiques compilés."],
  ["Git + venv","Déploiement","Cycle de déploiement simple par synchronisation de dépôt et exécution isolée."],
 ],
 [1900,1900,5560],
 "Choix des outils et justifications"));
push(H2("5.2 Architecture technique et déploiement"));
push(P("L'application est destinée à être hébergée sur le matériel personnel de l'utilisateur (serveur Linux dédié, NAS ou mini-PC). Un reverse proxy Nginx redirige le trafic web externe vers le port de l'API locale (8000) et sert directement les fichiers statiques compilés du frontend. Le diagramme de déploiement ci-dessous présente la répartition physique des composants."));
push(...FIG("deploy.png","Diagramme de déploiement",640,440));
push(H2("5.3 Conception de la sécurité"));
push(P("La sécurité a été pensée dès la conception. Les mots de passe sont hachés avec PBKDF2 (sel unique, nombre d'itérations paramétrable). L'authentification repose sur des jetons signés HMAC-SHA256 à durée de vie limitée. Les endpoints sensibles sont protégés par une limitation de débit (rate limiting) afin de contrer les attaques par force brute. Les jetons invités sont scopés : ils ne portent que la liste des contenus autorisés et chaque requête de streaming vérifie cette appartenance. Enfin, toute lecture ou écriture de fichier est contrôlée pour rester sous le dossier média autorisé (protection contre la traversée de répertoire), et des en-têtes HTTP de sécurité sont systématiquement ajoutés."));
push(H2("5.4 Modèle physique des données"));
push(P("La base relationnelle SQLite est organisée autour de six tables principales : users, contents, share_links, share_link_contents, share_link_usages, audit_logs et app_settings. Les clés étrangères sont activées au niveau de chaque connexion (PRAGMA foreign_keys = ON). L'extrait de schéma SQL est fourni en annexe B."));

// ============== 6. RÉALISATION ==============
push(H1("6. Réalisation"));
push(H2("6.1 Organisation du code"));
push(P("Le code source est organisé en deux parties. Le backend, sous backend/app, suit le principe d'une responsabilité par module : auth (jetons et contrôle d'accès), db (accès aux données et migrations), streaming (lecture HTTP Range et HLS), hls (sessions de transcodage), transcoder (conversion MKV→MP4), optimizer (worker planifié), search (recherche bibliothèque et disque), overseerr (métadonnées externes), upload (réception des fichiers), scanner, content_ids et media_naming. Le frontend, sous frontend/src, regroupe l'application Vue et ses composants (bibliothèque, lecteur, paramètres, modales d'association et de partage)."));
push(H2("6.2 Modules backend principaux"));
push(H3("6.2.1 Accès aux données (db)"));
push(P("Le module db centralise tout l'accès à la base. Il expose un gestionnaire de connexion asynchrone qui encapsule chaque transaction, active les clés étrangères et garantit une fermeture hermétique dans un bloc finally. Il porte également la création des tables, la migration progressive du schéma et l'ensemble des fonctions métier (création et recherche de contenus, gestion des liens de partage, journalisation d'audit, lecture/écriture des réglages). Toutes les requêtes sont paramétrées, ce qui prévient les injections SQL."));
push(H3("6.2.2 Authentification (auth)"));
push(P("Le module auth implémente la création et la vérification des jetons signés (HMAC-SHA256), les dépendances de contrôle d'accès (utilisateur courant, administrateur requis) et la limitation de débit. Il fournit aussi la fabrique du jeton invité scopé, dont le claim cids restreint l'accès aux seuls contenus d'un lien de partage."));
push(H3("6.2.3 Diffusion (streaming) et transcodage (hls, transcoder, optimizer)"));
push(P("Le module streaming gère la lecture directe : analyse de l'en-tête Range, réponse 206 Partial Content et lecture par morceaux pour borner la consommation mémoire. Il expose également les points d'entrée HLS. Le module hls orchestre des sessions FFmpeg : il sonde les codecs, décide du mode de lecture, démarre la génération de segments et nettoie les sessions inactives via un « reaper ». Le module transcoder réalise la conversion MKV→MP4 web, tandis que le module optimizer exécute le worker planifié d'optimisation des fichiers durant les heures creuses."));
push(H3("6.2.4 Recherche (search) et métadonnées (overseerr)"));
push(P("Le module search fournit la recherche dans la bibliothèque indexée (classement par pertinence) ainsi que la recherche récursive de fichiers sur le disque. Le module overseerr interroge l'API tierce et normalise les résultats (affiche, bannière, synopsis, année, identifiant TMDb) pour alimenter l'association de métadonnées, en gérant le percent-encodage strict des requêtes et la remontée fidèle des erreurs."));
push(H3("6.2.5 Réception des fichiers (upload) et nommage (content_ids, media_naming)"));
push(P("Le module upload reçoit les fichiers par morceaux et les range dans l'arborescence films/séries. Les modules content_ids et media_naming garantissent l'unicité des identifiants et la cohérence des noms physiques, socle de l'indexation résiliente."));
push(H2("6.3 Fonctionnalités phares"));
push(H3("6.3.1 Transcodage HLS à la volée"));
push(P("Lorsqu'un média n'est pas lisible nativement, le serveur démarre une session FFmpeg produisant des segments .ts et une playlist .m3u8 consommés par hls.js. Un « reaper » périodique ferme les sessions inactives afin de libérer les ressources. La décision de lecture est prise par une fonction qui, en cas d'indisponibilité de ffprobe, retombe gracieusement sur la lecture directe pour ne jamais renvoyer d'erreur serveur."));
push(H3("6.3.2 Partage temporaire multi-contenus"));
push(P("L'administrateur sélectionne plusieurs contenus à l'aide de cases à cocher ; le lien est stocké avec une table de jointure et des contraintes (expiration, quota, code PIN haché). À l'usage, le serveur émet un jeton invité dont le claim cids liste les contenus autorisés ; l'invité accède à une véritable mini-bibliothèque et peut visionner réellement les médias."));
push(H3("6.3.3 Recherche par pertinence"));
push(P("La recherche dans la bibliothèque classe les résultats par pertinence, à la manière d'un moteur de recherche : un titre exact prime sur un titre commençant par la requête, lui-même prioritaire sur une correspondance par mot, puis par sous-chaîne, puis sur l'identifiant. La barre de recherche propose en complément, après un court délai, des suggestions externes issues d'Overseerr."));
push(H2("6.4 Problèmes rencontrés et solutions"));
push(...TBL(
 ["Problème","Solution"],
 [
  ["Concurrence SQLite : exceptions sous accès asynchrones concurrents.","Gestionnaire de contexte _connect() encapsulant chaque transaction, activation des clés étrangères et fermeture dans un bloc finally."],
  ["Évolution du schéma sans outil de migration externe.","Introspection au démarrage (PRAGMA table_info) et application conditionnelle de requêtes ALTER TABLE, sans perte de données."],
  ["Renforcement du hachage des mots de passe sans réinitialisation générale.","Stratégie de migration « lazy » à la connexion : l'ancien hachage SHA-256 est ré-encodé en PBKDF2 de façon transparente."],
  ["Encodage de la requête Overseerr (« query must be url encoded »).","Percent-encodage strict (espaces en %20) au lieu de l'encodage de formulaire."],
  ["Erreur 500 et CORS sur l'endpoint d'information de lecture.","Suppression de la sonde ffprobe lorsque le transcodage est désactivé et repli gracieux, supprimant la cause de l'erreur."],
 ],
 [3300,6060],
 "Synthèse des problèmes rencontrés et des solutions apportées"));

// ============== 7. TESTS ==============
push(H1("7. Tests et validation"));
push(H2("7.1 Stratégie de test"));
push(P("La validation a combiné des tests fonctionnels manuels (parcours utilisateur de bout en bout), des vérifications de sécurité et des contrôles de robustesse sous conditions dégradées (absence de ffprobe, fichier manquant, lien expiré). L'objectif n'était pas une couverture exhaustive automatisée — identifiée comme une perspective d'amélioration — mais la validation des chemins critiques."));
push(H2("7.2 Plan de tests fonctionnels"));
push(...TBL(
 ["Réf.","Cas de test","Résultat attendu"],
 [
  ["T-01","Connexion avec identifiants valides","Jeton émis, accès au tableau de bord."],
  ["T-02","Connexion avec mot de passe erroné","Refus 401, message inline, pas de navigation."],
  ["T-03","Lecture d'un MP4 H.264","Lecture directe (HTTP 206)."],
  ["T-04","Lecture d'un MKV H.265","Bascule automatique en HLS."],
  ["T-05","Création d'un lien multi-contenus","Lien généré, contenus associés."],
  ["T-06","Accès invité avec PIN correct","Mini-bibliothèque accessible, usage tracé."],
  ["T-07","Accès invité à un contenu hors lien","Refus 403 (jeton scopé)."],
  ["T-08","Lien expiré / quota atteint","Accès refusé avec message explicite."],
  ["T-09","Recherche « spider man »","Résultats classés par pertinence."],
  ["T-10","Association Overseerr d'un film","Affiche et synopsis enregistrés."],
 ],
 [1000,4200,4160],
 "Plan de tests fonctionnels"));
push(H2("7.3 Tests de sécurité"));
push(P("Les tests de sécurité ont porté sur la résistance à la force brute (déclenchement du rate limiting après plusieurs tentatives), l'impossibilité d'accéder à un fichier hors du dossier média (tentative de traversée de répertoire de type ../), la validité et l'expiration des jetons, le rejet d'un jeton falsifié (signature invalide) et le cloisonnement des jetons invités (refus 403 d'un contenu hors du périmètre du lien)."));
push(H2("7.4 Tests de robustesse et de performance"));
push(P("Des tests de robustesse ont vérifié le comportement du système sous conditions dégradées : absence de l'exécutable ffprobe (repli en lecture directe sans erreur 500), fichier média supprimé du disque (réponse 404 maîtrisée), lien de partage expiré ou épuisé. Côté performance, la lecture par morceaux et la nature asynchrone du serveur ont été éprouvées par plusieurs visionnages simultanés ; le worker d'optimisation s'efface lorsqu'un fichier est en cours de lecture afin de ne pas dégrader l'expérience. La principale limite identifiée reste le coût CPU du transcodage logiciel, qui borne le nombre de transcodages à la volée concurrents — d'où la perspective d'une accélération matérielle."));

// ============== 8. DÉPLOIEMENT ==============
push(H1("8. Déploiement et exploitation"));
push(H2("8.1 Procédure de mise en service"));
push(P("La mise en service du MVP s'effectue via un workflow basé sur Git. L'administrateur clone le dépôt sur le serveur de production, configure l'environnement virtuel Python (python -m venv venv), installe les dépendances (pip install -r requirements.txt) et génère les fichiers de production du frontend (npm run build). Nginx redirige ensuite le trafic externe vers le port 8000 de l'API et sert les fichiers statiques compilés."));
push(H2("8.2 Configuration"));
push(P("La configuration s'effectue par variables d'environnement (secret applicatif, dossier média, paramètres de sécurité) et par la table app_settings (dossiers films/séries, presets de transcodage, configuration Overseerr). Les valeurs sensibles ne sont jamais journalisées en clair."));
push(H2("8.3 Maintenance, sauvegardes et journalisation"));
push(P("La portabilité de SQLite simplifie les sauvegardes : il suffit de copier le fichier de base et le dossier média. La journalisation d'audit, consultable depuis l'interface d'administration, centralise les actions sensibles. Le worker d'optimisation assure une maintenance proactive des fichiers."));
push(H2("8.4 Formation et suivi"));
push(P("L'interface a été épurée afin d'offrir une prise en main immédiate, ne nécessitant aucune formation pour les invités. Pour l'administrateur, le suivi s'appuie sur un guide d'administration maintenu sur le Wiki GitHub du projet et sur la consultation du journal d'audit."));

// ============== 9. GESTION DE PROJET ==============
push(H1("9. Gestion de projet"));
push(P("Le projet a été conduit de manière itérative et incrémentale, chaque itération livrant un incrément fonctionnel testable. Le tableau suivant résume le déroulement."));
push(...TBL(
 ["Phase","Contenu","Livrable"],
 [
  ["Cadrage","Interviews, étude de l'existant, cahier des charges.","Cahier des charges, périmètre MVP."],
  ["Analyse & conception","Cas d'utilisation, MCD/MLD, architecture.","Modèles UML/Merise, schéma de données."],
  ["Socle technique","API FastAPI, base SQLite, authentification.","Backend de base sécurisé."],
  ["Streaming","Lecture directe, transcodage HLS, lecteur.","Visionnage fonctionnel."],
  ["Partage & invités","Liens temporaires multi-contenus, accès invité.","Partage sécurisé."],
  ["Expérience","Bibliothèque type Plex, recherche, Overseerr, thème.","Interface aboutie."],
  ["Finalisation","Tests, déploiement, documentation, rapport.","Application livrée + rapport."],
 ],
 [1700,4500,3160],
 "Déroulement du projet"));

// ============== 10. ÉVALUATION ==============
push(H1("10. Évaluation du travail"));
push(H2("10.1 Autocritique"));
push(P("La démarche itérative a permis de bâtir un socle solide tout en s'adaptant aux retours. Une catégorisation initiale plus stricte des métadonnées dès la première interview aurait toutefois évité quelques ajustements de schéma en cours de route — ajustements absorbés sans douleur grâce au mécanisme de migration progressive. Le choix d'un déploiement Git pour le MVP a permis de respecter les délais en contournant la complexité d'une infrastructure conteneurisée non finalisée."));
push(H2("10.2 Points de satisfaction"));
push(...BULL([
 "une alternative réellement fonctionnelle, libre et respectueuse de la vie privée ;",
 "des différenciateurs absents du marché, notamment le partage temporaire multi-contenus ;",
 "une manipulation concrète des flux vidéo via le transcodage HLS à la volée ;",
 "une architecture asynchrone solide et une sécurité soignée ;",
 "une expérience utilisateur aboutie (interface type Plex, mode sombre, responsive)."]));
push(H2("10.3 Limites identifiées"));
push(...BULL([
 "le seek dans un flux HLS transcodé séquentiellement reste perfectible ;",
 "l'absence d'accélération matérielle limite le nombre de transcodages simultanés ;",
 "la couverture de tests automatisés est à renforcer."]));

// ============== 11. CONCLUSION ==============
push(H1("11. Conclusion et perspectives"));
push(P("Ce travail de fin d'études démontre la viabilité d'une alternative de streaming libre, modulaire et respectueuse de la vie privée. Vellucast répond aux besoins identifiés des utilisateurs avancés et propose des fonctionnalités — partage temporaire multi-contenus, transcodage planifié et à la volée, indexation résiliente — que les solutions du marché n'offrent pas nativement. Sur le plan personnel, il m'a permis d'acquérir une solide expérience pratique de l'architecture asynchrone, de l'administration Linux et de la manipulation de flux vidéo."));
push(P("Les perspectives prioritaires concernent le support de l'accélération matérielle GPU (NVENC / QuickSync), un HLS adaptatif avec seek instantané, la gestion des métadonnées locales (NFO) et des pistes multiples, la conteneurisation Docker Compose, des applications clientes natives, et la mise en place de tests automatisés et d'intégration continue. En une phrase, Vellucast vise un objectif simple : reprendre le contrôle de sa médiathèque."));

// ============== 12. BIBLIOGRAPHIE ==============
push(H1("12. Bibliographie"));
push(...BULL([
 "Documentation officielle FastAPI — https://fastapi.tiangolo.com",
 "Documentation officielle Vue.js — https://vuejs.org",
 "Documentation FFmpeg — https://ffmpeg.org/documentation.html",
 "Spécification HTTP Live Streaming (HLS) — RFC 8216.",
 "Documentation SQLite — https://www.sqlite.org/docs.html",
 "Documentation API Overseerr — https://api-docs.overseerr.dev",
 "Code de droit économique (Belgique) — livre XI, propriété intellectuelle.",
 "NIST SP 800-132 — Recommandation pour la dérivation de clés (PBKDF2).",
]));

// ============== 13. GLOSSAIRE ==============
push(H1("13. Glossaire"));
push(...TBL(
 ["Terme","Définition"],
 [
  ["Auto-hébergement","Fait d'héberger soi-même un service sur son propre matériel plutôt que chez un fournisseur."],
  ["BYOC","Bring Your Own Content : l'application ne fournit aucun contenu, fourni par l'utilisateur."],
  ["Codec","Algorithme d'encodage/décodage d'un flux audio ou vidéo (H.264, H.265, AAC…)."],
  ["HLS","HTTP Live Streaming : diffusion par segments décrits dans une playlist .m3u8."],
  ["Transcodage","Ré-encodage d'un flux d'un format vers un autre."],
  ["JWT / jeton signé","Jeton d'authentification dont l'intégrité est garantie par une signature (HMAC)."],
  ["PBKDF2","Fonction de dérivation de clé utilisée pour hacher robustement les mots de passe."],
  ["Reverse proxy","Serveur intermédiaire redirigeant les requêtes vers un service interne."],
  ["MCD / MLD","Modèles conceptuel / logique des données de la méthode Merise."],
 ],
 [2200,7160],
 "Glossaire des termes techniques"));

// ============== ANNEXES ==============
push(H1("Annexe A — Guide de déploiement"));
push(...CODE([
 "# 1. Cloner le dépôt",
 "git clone https://github.com/ElFifux540/vellucast.git && cd vellucast",
 "",
 "# 2. Backend",
 "cd backend && python -m venv venv && source venv/bin/activate",
 "pip install -r requirements.txt",
 "export MEDIA_FOLDER=/srv/media APP_SECRET=... APP_ENV=prod",
 "uvicorn app.main:app --host 127.0.0.1 --port 8000",
 "",
 "# 3. Frontend",
 "cd ../frontend && npm install && npm run build",
 "",
 "# 4. Nginx : proxy_pass vers http://127.0.0.1:8000 + service du dossier dist/",
],"Procédure de déploiement (résumé)"));
push(H1("Annexe B — Extraits de code"));
push(...CODE([
 "async def _connect():",
 "    db = await aiosqlite.connect(DB_PATH)",
 "    await db.execute('PRAGMA foreign_keys = ON')",
 "    return db   # encapsulé dans un gestionnaire de contexte (fermeture en finally)",
],"B.1 — Gestionnaire de connexion (concurrence SQLite)"));
push(...CODE([
 "async def decide_playback(media_path, *, transcode_enabled):",
 "    if not transcode_enabled:",
 "        return {'mode': 'direct', 'reason': 'transcodage désactivé'}",
 "    try:",
 "        info = await probe_codecs(media_path)",
 "    except (FileNotFoundError, NotImplementedError, OSError):",
 "        return {'mode': 'direct', 'reason': 'analyse indisponible'}",
 "    directly = container_ok and video_ok and audio_ok",
 "    return {'mode': 'direct' if directly else 'hls', ...}",
],"B.2 — Décision lecture directe / HLS"));
push(...CODE([
 "def _relevance_key(content, q):",
 "    title = content['title'].lower()",
 "    if title == q: rank = 0",
 "    elif title.startswith(q): rank = 1",
 "    elif any(w.startswith(q) for w in title.split()): rank = 2",
 "    elif q in title: rank = 3",
 "    else: rank = 4",
 "    return (rank, title)",
],"B.3 — Classement des résultats par pertinence"));

// ============== DOC ==============
const doc = new Document({
  creator:"Julien Hoorens", title:"Rapport TFE — Vellucast",
  styles:{
    default:{ document:{ run:{ font:FONT, size:22 } } },
    paragraphStyles:[
      { id:"Heading1", name:"Heading 1", basedOn:"Normal", next:"Normal", quickFormat:true, run:{size:32,bold:true,font:FONT,color:"312E81"}, paragraph:{spacing:{before:240,after:160}, outlineLevel:0} },
      { id:"Heading2", name:"Heading 2", basedOn:"Normal", next:"Normal", quickFormat:true, run:{size:26,bold:true,font:FONT,color:"4338CA"}, paragraph:{spacing:{before:200,after:120}, outlineLevel:1} },
      { id:"Heading3", name:"Heading 3", basedOn:"Normal", next:"Normal", quickFormat:true, run:{size:23,bold:true,font:FONT,color:"1E293B"}, paragraph:{spacing:{before:160,after:100}, outlineLevel:2} },
    ]
  },
  numbering:{ config:[
    { reference:"bul", levels:[{level:0,format:LevelFormat.BULLET,text:"•",alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:600,hanging:300}}}}] },
    { reference:"num", levels:[{level:0,format:LevelFormat.DECIMAL,text:"%1.",alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:600,hanging:300}}}}] },
  ]},
  sections:[{
    properties:{ page:{ size:{width:12240,height:15840}, margin:{top:1440,right:1440,bottom:1440,left:1440} } },
    headers:{ default: new Header({ children:[ new Paragraph({ alignment:AlignmentType.RIGHT, children:[new TextRun({text:"Vellucast — TFE",size:16,color:"94A3B8"})] }) ] }) },
    footers:{ default: new Footer({ children:[ new Paragraph({ alignment:AlignmentType.CENTER, children:[ new TextRun({text:"Julien Hoorens   ·   ",size:16,color:"94A3B8"}), new TextRun({children:["Page ", PageNumber.CURRENT],size:16,color:"94A3B8"}) ] }) ] }) },
    children
  }]
});
Packer.toBuffer(doc).then(b=>{ fs.writeFileSync(OUT,b); console.log("WROTE",OUT,(b.length/1024).toFixed(0)+"KB"); });
