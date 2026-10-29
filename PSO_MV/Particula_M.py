import random as rd
import numpy as np

#PSO MultiVariable
class particula:
    #Constructor MultiVariable
    def __init__(self, n_variables, lim_inf, lim_sup,info=False):
        self.n_variables = n_variables
        self.lim_inf = lim_inf
        self.lim_sup = lim_sup

        self.posicion = np.empty(n_variables, dtype=float)
        self.velocidad = np.zeros(n_variables, dtype=float)
        self.valor = None

        self.mej_valor = None
        self.mej_posicion = None
    
        if self.lim_inf is not None and not isinstance(self.lim_inf,np.ndarray):
            self.lim_inf = np.array(self.lim_inf)
        if self.lim_inf is None:
            self.lim_inf = np.repeat(-10**3,self.n_variables)
        
        if self.lim_sup is not None and not isinstance(self.lim_sup,np.ndarray):
            self.lim_sup = np.array(self.lim_sup)
        if self.lim_sup is None:
            self.lim_sup = np.repeat(+10**3,self.n_variables)
        
        for i in np.arange(self.n_variables):
            self.posicion[i] = rd.uniform(
                self.lim_inf[i],
                self.lim_sup[i]
            )

        self.velocidad = np.zeros(self.n_variables, dtype=float)

        if info:
            print("Partícula creada")
            print("------------------")
            print("Posición: " + str(self.posicion))
            print("Límites inferiores: " + str(self.lim_inf))
            print("Límites superiores: " + str(self.lim_sup))
            print("Velocidad: " + str(self.velocidad))
            print("")           
    
    def _procesar_resultado(self, resultado):   
        valor = np.asarray(resultado).squeeze()
        if valor.size != 1:
            raise ValueError("La función objetivo debe devolver un escalar")
        return float(valor)

    def evaluar_particula(self, optimizacion,funcion_objetivo,info=False):
        if optimizacion not in ['Maximización','Minimización']:
            raise Exception('El argumento optimizacion debe ser: maximizar o minimizar')
        
        try:
            self.valor = self._procesar_resultado(funcion_objetivo(self.posicion))
        except TypeError as e_original:
            try:
                self.valor = self._procesar_resultado(funcion_objetivo(*self.posicion))
            except TypeError:
                raise TypeError(
                    f'La función objetivo falló con ambos formatos. '
                    f'Error original: {e_original}'
                ) from e_original 

        if self.mej_valor is None:
            self.mej_posicion = np.copy(self.posicion)
            self.mej_valor = float(self.valor)
        else:
            if optimizacion == 'Minimización':
                if self.valor < self.mej_valor:
                    self.mej_valor = float(self.valor)
                    self.mej_posicion = np.copy(self.posicion)
            elif optimizacion == 'Maximización':
                if self.valor > self.mej_valor:
                    self.mej_valor = float(self.valor)
                    self.mej_posicion = np.copy(self.posicion)

        if info:
            print("La partícula ha sido evaluada")
            print("-----------------------------")
            print("Valor actual: " + str(self.valor))
            print("")

    
    def actualizar_componentes(self, gbest_posicion, w=0.9, c1=1.5, c2=1.5, mu=0.5, info=False):
        r1 = np.random.uniform(0, 1, self.n_variables)
        r2 = np.random.uniform(0, 1, self.n_variables)

        if self.mej_posicion is None:
            raise RuntimeError("La partícula debe evaluarse antes de actualizar componentes")

        new_vel = (w * self.velocidad) + (c1 * r1 * (self.mej_posicion - self.posicion)) + (c2 * r2 * (gbest_posicion - self.posicion))

        self.velocidad = np.copy(new_vel)

        self.posicion = self.velocidad + self.posicion

        for i in np.arange(len(self.posicion)):
            if self.posicion[i] < self.lim_inf[i]:
                self.posicion[i] = self.lim_inf[i]
                 self.velocidad[i] = abs(self.velocidad[i]) * mu

            if self.posicion[i] > self.lim_sup[i]:
                self.posicion[i] = self.lim_sup[i]
                self.velocidad[i] = -abs(self.velocidad[i]) * mu

        if info:
            print("La partícula se ha desplazado")
            print("-----------------------------")
            print("Nueva posición: " + str(self.posicion))
            print("")

