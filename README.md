FR

Cette application Streamlit a été développée dans le cadre de mon stage de recherche de quatre mois à l'Imperial College London. Son objectif est de quantifier et visualiser les erreurs de mesure d'un instrument optique complexe, afin de fournir les données d'analyse nécessaires à la publication d'un article scientifique.

L'application est une interface web développée en Python qui fait office de jumeau numérique pour l'instrument de mesure. Son rôle est de permettre aux utilisateurs de simuler différents écoulements de particules et d'évaluer les biais du capteur de manière visuelle, sans avoir à interagir directement avec le code source.

L'outil s'articule autour de deux modes de fonctionnement. Le premier est un mode paramétrique dans lequel l'algorithme balaie une grille de valeurs mathématiques, comme les vitesses moyennes axiale et radiale, pour générer des graphiques d'erreur en trois dimensions. Cela permet d'observer l'évolution théorique de l'erreur en fonction de la variation des paramètres de l'écoulement.

Le second mode repose sur des données expérimentales. L'utilisateur sélectionne une coordonnée physique précise à l'intérieur du séchoir industriel à l'aide de menus déroulants. Le programme appelle alors la base de données correspondante pour générer le nuage de particules propre à cette zone. L'interface affiche ensuite plusieurs visualisations interactives générées avec Plotly. On y trouve des nuages de points en trois dimensions qui séparent les particules acceptées des particules rejetées en fonction de leur diamètre et de leurs vitesses, ainsi que des cartes de chaleur identifiant les zones de l'écoulement les plus impactées par les filtres de l'appareil. En parallèle, l'application calcule et affiche des tableaux de métriques qui comparent les statistiques réelles du fluide virtuel aux données faussées par le capteur, fournissant ainsi le pourcentage d'erreur exact sur chaque grandeur macroscopique.


EN

This Streamlit application was developed during my four-month research internship at Imperial College London. Its purpose is to quantify and visualize the measurement errors of a complex optical instrument, in order to provide the necessary analytical data for the publication of a research paper.

The application is a web interface developed in Python that acts as a digital twin for the measurement instrument. Its role is to allow users to simulate different particle flows and visually evaluate the sensor's biases, without having to interact directly with the source code.

The tool is built around two operating modes. The first is a parametric mode in which the algorithm sweeps through a grid of mathematical values, such as mean axial and radial velocities, to generate three-dimensional error graphs. This makes it possible to observe the theoretical evolution of the error based on the variation of the flow parameters.

The second mode relies on experimental data. The user selects a specific physical coordinate inside the industrial dryer using drop-down menus. The program then calls the corresponding database to generate the particle cloud specific to that area. The interface then displays several interactive visualizations generated with Plotly. These include three-dimensional scatter plots that separate accepted particles from rejected ones based on their diameter and velocities, as well as heatmaps identifying the flow areas most impacted by the device's filters. In parallel, the application calculates and displays metric tables that compare the actual statistics of the virtual fluid to the skewed data from the sensor, thereby providing the exact error percentage for each macroscopic variable.
