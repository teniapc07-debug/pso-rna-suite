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
        self.valor = np.empty(1, dtype=float)

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
    
    def evaluar_particula(self, optimizacion,funcion_objetivo,info=False):
        if optimizacion not in ['Maximización','Minimización']:
            raise Exception('El argumento optimizacion debe ser: maximizar o minimizar')

        try:
            self.valor = funcion_objetivo(self.posicion)
        except TypeError:
            try:
                self.valor = funcion_objetivo(*self.posicion)
            except TypeError:
                raise TypeError('La función objetivo debe aceptar un array o los valores de cada variable')
        
        if self.mej_valor is None:
            self.mej_posicion = np.copy(self.posicion)
            self.mej_valor = np.copy(self.valor)
        else:
            if optimizacion == 'Minimización':
                if self.valor < self.mej_valor:
                    self.mej_valor = np.copy(self.valor)
                    self.mej_posicion = np.copy(self.posicion)
            elif optimizacion == 'Maximización':
                if self.valor > self.mej_valor:
                    self.mej_valor = np.copy(self.valor)
                    self.mej_posicion = np.copy(self.posicion)

        if info:
            print("La partícula ha sido evaluada")
            print("-----------------------------")
            print("Valor actual: " + str(self.valor))
            print("")

    
    def actualizar_componentes(self, gbest_posicion, w=0.9, c1=1.5, c2=1.5, info=False):
        r1 = np.random.uniform(0,1)
        r2 = np.random.uniform(0,1)

        new_vel = (w * self.velocidad) + (c1 * r1 * (self.mej_posicion - self.posicion)) + (c2 * r2 * (gbest_posicion - self.posicion))

        self.velocidad = np.copy(new_vel)

        self.posicion = self.velocidad + self.posicion

        for i in np.arange(len(self.posicion)):
            if self.posicion[i] < self.lim_inf[i]:
                self.posicion[i] = self.lim_inf[i]
                self.velocidad[i] = 0
            if self.posicion[i] > self.lim_sup[i]:
                self.posicion[i] = self.lim_sup[i]
                self.velocidad[i] = 0

        if info:
            print("La partícula se ha desplazado")
            print("-----------------------------")
            print("Nueva posición: " + str(self.posicion))
            print("")

if __name__ == "__main__":
    example = partícula(
        n_variables=2,
        lim_inf=[10,-2],
        lim_sup=[-7,9],
        info = False
    )
    print(example)
    def function(x_0,x_1):
        f = (x_0**2) + (x_1**2)
        return (f)
    example.evaluar_particula(
        funcion_objetivo=function,
        optimizacion='Minimización',
        info=True,
    )
    example.actualizar_componentes(
        gbest_posicion=np.array([-100,100]),
        info=True,
    )