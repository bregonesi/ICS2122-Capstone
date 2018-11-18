# ICS2122-Capstone - Grupo 12

 - Las bases de datos tienen que estar en la carpeta `datos` tal como se entrega

 - Los resultados se exportan a la carpeta `resultados` en diferentes formatos. Alternativamente se pueden imprimir en consola descomentando la linea `1260`, `1263` y `1267`. Si se descomentan estas se sugiere comentar las lineas `1261`, `1262` y `1266` respectivamente.

 - Existen dos variables en el programa:
 -> `maximo_de_partidos`: Indica el máximo número de partidos que un arbitro puede arbitrar en la temporada. Un valor posible es `40`
 -> `rango_de_escoger_arbitros`: Se selecciona un arbitro 'optimo', luego de eso se busca hasta en un rango maximo (por ejemplo 10%) de costo si es que existe algun arbitro que no haya arbitrado nunca, y, si es así, se escoge el que no ha arbitrado nunca. Un valor posible sería `1.10`, que indica un 10% más.
 Estas dos variables se entregan comentadas y se pueden modificar en la linea `1254` y `1255` respectivamente.

 - Para ejecutar el programa solo basta con tener la base de datos y los valores posibles en las variables mencionadas anteriormente. Se ejecuta corriendo el archivo `clases.py`.
