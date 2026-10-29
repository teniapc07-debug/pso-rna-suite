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
        self.mej_part = None

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
        for p in self.particulas:
            p.evaluar_particula(
                optimizacion=optimizacion,
                funcion_objetivo=funcion_objetivo,
                info=info
            )
        
        if optimizacion == 'Minimización':
            self.mej_part = copy.deepcopy(
                min(self.particulas, key=lambda p: float(np.asarray(p.mej_valor).squeeze()))
            )
        elif optimizacion == 'Maximización':
            self.mej_part = copy.deepcopy(
                max(self.particulas, key=lambda p: float(np.asarray(p.mej_valor).squeeze()))
            )
        else:
            raise ValueError("optimizacion debe ser 'Minimización' o 'Maximización'")

        self.mej_posicion = copy.deepcopy(self.mej_part.mej_posicion)
        self.mej_valor = float(np.asarray(self.mej_part.mej_valor).squeeze())

    def mover_enjambre(self, w, c1, c2, mu=0.5, info=False):
        for i in range(self.n_particulas):
            self.particulas[i].actualizar_componentes(
                gbest_posicion = self.mej_posicion,
                w=w,
                c1=c1,
                c2=c2,
                mu=mu,
                info=info,
            )

    def optimizar(self,funcion_objetivo, optimizacion, n_iteraciones, w=0.9, c1=1.5, c2=1.5, mu=0.5, info=False,w_i=0.9,w_f=0.4,reduccion_w=True, rondas_parada=10, parada_temprana=False, tolerancia=1e-6, carpeta_salida="resultados_pso", iteracion_callback=None):
        if not isinstance(n_iteraciones, (int, np.integer)) or n_iteraciones <= 0:
            raise ValueError("n_iteraciones debe ser un entero positivo")
        n_iteraciones = int(n_iteraciones)

        if not isinstance(rondas_parada, (int, np.integer)) or rondas_parada < 1:
            raise ValueError("rondas_parada debe ser un entero positivo")
                
        inicio = tm.time()
        self.hist_mej_valor.clear()
        self.hist_mejor_posicion.clear()
        self.diferecia_mejor_valor.clear()

        self.mej_part = None
        self.mej_posicion = None
        self.mej_valor = None

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
                    logger.exception("Error en iteracion_callback")

            #-------------------------------------------------------------------------------------------
            if i > 0:
                diferencia = self.hist_mej_valor[i] - self.hist_mej_valor[i - 1]
                self.diferecia_mejor_valor.append(diferencia)
            
            if parada_temprana and len(self.diferecia_mejor_valor) >= rondas_parada:
                ultimas = np.asarray(
                    self.diferecia_mejor_valor[-rondas_parada:],
                    dtype=float
                )
                if np.all(np.abs(ultimas) < tolerancia):
                    logger.info(
                        f"Parada temprana en la iteración {i + 1}"
                    )
                    break
            #--------------------------------------------------------------------------------------------

            if reduccion_w:
                if n_iteraciones > 1:
                    w = w_i + (i / (n_iteraciones - 1)) * (w_f - w_i)
                else:
                    w = w_i

            self.mover_enjambre(
                w = w,
                c1 = c1,
                c2 = c2,
                mu = mu,
                info = False,
            )
            
        self.dtframe = pd.DataFrame(
            {
                "Iteracion": np.arange(1, len(self.hist_mej_valor) + 1),
                "Mejor_Valor": self.hist_mej_valor,
            }
        )
        for j in range(self.n_variables):
            self.dtframe[f"x{j+1}"] = [pos[j] for pos in self.hist_mejor_posicion]

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
