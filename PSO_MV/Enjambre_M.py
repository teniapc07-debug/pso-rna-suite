import numpy as np
import copy
import time as tm
import pandas as pd
import logging
from pathlib import Path
from .Particula_M import particula

logger = logging.getLogger(__name__)

class enjambre:
    def __init__(self,n_particulas, n_variables, lim_inf, lim_sup,info=False):
        self.n_particulas = n_particulas
        self.n_variables = n_variables
        self.lim_inf = lim_inf
        self.lim_sup = lim_sup

        self.particulas = []
        self.mej_posicion = None
        self.mej_valor = None
        self.mje_part = None

        self.hist_mej_valor = []
        self.hist_mejor_posicion = []
        self.diferecia_mejor_valor = []

        self.iteracion_optimo = None
        self.valor_optimo = None
        self.posicion_optima = None

        self.dtframe = None


        if self.lim_inf is not None and not isinstance(self.lim_inf,np.ndarray):
            self.lim_inf = np.array(self.lim_inf)
        
        if self.lim_sup is not None and not isinstance(self.lim_sup,np.ndarray):
            self.lim_sup = np.array(self.lim_sup)
        
        for i in range(self.n_particulas):
            part_i = particula(
                n_variables=self.n_variables,
                lim_inf=self.lim_inf,
                lim_sup=self.lim_sup,
                info=info,
            )
            self.particulas.append(part_i)
    
    def evaluar_enjambre(self,optimizacion,funcion_objetivo,info=False):
        for i in range(self.n_particulas):
            self.particulas[i].evaluar_particula(
                optimizacion=optimizacion,
                funcion_objetivo=funcion_objetivo,
                info=info
            )
        self.mej_part = copy.deepcopy(self.particulas[0])
        for i in range(self.n_particulas):
            if optimizacion == 'Minimización':
                if self.particulas[i].valor < self.mej_part.valor:
                    self.mej_part = copy.deepcopy(self.particulas[i])
            elif optimizacion == 'Maximización':
                if self.particulas[i].valor > self.mej_part.valor:
                    self.mej_part = copy.deepcopy(self.particulas[i])
        self.mej_posicion = copy.deepcopy(self.mej_part.posicion)
        self.mej_valor = copy.deepcopy(self.mej_part.valor)

    def mover_enjambre(self, w, c1, c2,info):
        for i in range(self.n_particulas):
            self.particulas[i].actualizar_componentes(
                gbest_posicion = self.mej_posicion,
                w=w,
                c1=c1,
                c2=c2,
                info=info,
            )

    def optimizar(self,funcion_objetivo, optimizacion, n_iteraciones, w=0.9, c1=1.5, c2=1.5, info=False,w_i=0.9,w_f=0.4,reduccion_w=True, rondas_parada=10, parada_temprana=False, tolerancia=1e-6, carpeta_salida="resultados_pso", iteracion_callback=None):
        inicio = tm.time()
        for i in range(n_iteraciones):
            if info:
                logger.info(f"Iteracion: {i+1}/{n_iteraciones}")
                logger.info("-----------------------------")
            self.evaluar_enjambre(
                optimizacion=optimizacion,
                funcion_objetivo=funcion_objetivo,
                info=info,
            )
            self.hist_mej_valor.append(copy.deepcopy(self.mej_valor))
            self.hist_mejor_posicion.append(copy.deepcopy(self.mej_posicion))

            if iteracion_callback is not None:
                try:
                    iteracion_callback(i + 1, n_iteraciones, self.mej_valor)
                except Exception:
                    pass

            #-------------------------------------------------------------------------------------------
            if i == 0:
                self.diferecia_mejor_valor.append(None)
            else:
                diferencia = self.hist_mej_valor[i] - self.hist_mej_valor[i - 1]
                self.diferecia_mejor_valor.append(diferencia)
            
            if parada_temprana and i > rondas_parada:
                ultimas_diferencias = np.array(self.diferecia_mejor_valor[-(rondas_parada):])
                if all(ultimas_diferencias < tolerancia):
                    logger.info(f"Se ha alcanzado la condición de parada temprana en la iteración {i+1}")
                    break
            #--------------------------------------------------------------------------------------------

            if reduccion_w:
                w = w_i + (( n_iteraciones - (n_iteraciones - i))/n_iteraciones) * (w_f - w_i)

            self.mover_enjambre(
                w = w,
                c1 = c1,
                c2 = c2,
                info = False,
            )
            self.dtframe = pd.DataFrame(
                {
                    "Iteracion": np.arange(1, len(self.hist_mej_valor) + 1),
                    "Mejor_Valor": self.hist_mej_valor,
                    "Mejor_Posición": self.hist_mejor_posicion,
                }
            )
        
        final = tm.time()
        self.iteracion_optimo = i + 1
        self.tiempo_total = final - inicio

         # ---- guardar en carpeta dedicada ----
        carpeta = Path(carpeta_salida)
        carpeta.mkdir(parents=True, exist_ok=True)
        self.dtframe.to_csv(carpeta / "Historial_Enjambre.csv", index=False)

        self.valor_optimo = copy.deepcopy(self.mej_valor)
        self.posicion_optima = copy.deepcopy(self.mej_posicion)
         
        logger.info(f"Tiempo de optimizacion: {self.tiempo_total:.2f} segundos")
        logger.info(f"Iteraciones: {self.iteracion_optimo}")
        logger.info(f"Mejor valor encontrado: {(self.valor_optimo):.3f}")
        logger.info("Mejor posición encontrada:")
        for indice, valor in enumerate(np.asarray(self.posicion_optima).reshape(-1), start=1):
            logger.info(f"  x{indice}: {(valor):.3f}")
        logger.info("-" * 30)

if __name__ == "__main__":
    test = enjambre(
        n_particulas=5,
        n_variables=2,
        lim_inf=[-10,-5],
        lim_sup=[30,10],
        info = False
    )
    test.optimizar(
        n_iteraciones=10,
        optimizacion='Minimización',
        funcion_objetivo=lambda x,y: (x**2)+(y**2),
        w = 0.7,
        c1 = 1.5,
        c2 = 2,
        reduccion_w = True,
        info = False
    )