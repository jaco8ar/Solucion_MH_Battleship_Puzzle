
#restricciones basadas en https://www.csplib.org/Problems/prob014/models/sb.mzn.html
#Adaptadas con la ayuda de Gemini
#Elaboración propia de Estructura de objetos 


from enum import Enum

class Pieza(Enum):
    W = 1
    C = 2
    L = 3
    R = 4
    T = 5
    B = 6
    M = 7
    
    def es_barco(self):
        """Helper para saber si la pieza cuenta para las sumas"""
        return self != Pieza.W
    


class Direccion(Enum):
    VERTICAL = 1
    HORIZONTAL = 0

class Celda:
    def __init__(self, fila: int, columna: int, tipo: Pieza):
        self.fila = fila
        self.columna = columna
        self.tipo = tipo

class Objetivo:
    def __init__(self, ubicacion: tuple[int, int], partes: list[Celda]):
        self.ubicacion = ubicacion
        self.partes = partes

    # --- Funciones de validación independientes ---

    def validar_limites(self, tablero_obj) -> bool:
        """Verifica que todas las partes del barco estén dentro de la grilla."""
        filas_tablero, cols_tablero = tablero_obj.tamano_tablero
        
        for parte in self.partes:
            if not (0 <= parte.fila < filas_tablero and 0 <= parte.columna < cols_tablero):
                return False
        return True

    def validar_integridad(self, tablero_obj) -> bool:
        """
        Verifica solapamiento.
        Confirma que en el tablero realmente esté dibujada la pieza que este barco dice tener.
        Si hay otra pieza, significa que otro barco sobrescribió a este.
        """
        # Nota: Asumimos que validar_limites se ejecuta antes o se verifica aquí.
        # Para seguridad, verificamos límites rápido para evitar IndexError.
        filas_tablero, cols_tablero = tablero_obj.tamano_tablero
        matriz = tablero_obj.matriz
        
        for parte in self.partes:
            # Chequeo de seguridad bounds
            if not (0 <= parte.fila < filas_tablero and 0 <= parte.columna < cols_tablero):
                return False
            
            # Chequeo de integridad
            if matriz[parte.fila][parte.columna] != parte.tipo:
                return False
        return True

    def validar_espaciado(self, tablero_obj) -> bool:
        """
        Verifica que el barco esté rodeado de agua (excepto por sus propias piezas).
        Revisa los 8 vecinos de cada celda del barco.
        """
        filas_tablero, cols_tablero = tablero_obj.tamano_tablero
        matriz = tablero_obj.matriz
        
        # Set de coordenadas propias para auto-exclusión rápida
        mis_coordenadas = {(p.fila, p.columna) for p in self.partes}

        deltas = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]

        for parte in self.partes:
            # Si una parte está fuera del mapa, ignoramos el espaciado (ya fallará por límites)
            if not (0 <= parte.fila < filas_tablero and 0 <= parte.columna < cols_tablero):
                continue

            for df, dc in deltas:
                vecino_f, vecino_c = parte.fila + df, parte.columna + dc

                # Solo validamos si el vecino está dentro del tablero
                if 0 <= vecino_f < filas_tablero and 0 <= vecino_c < cols_tablero:
                    # Si el vecino NO soy yo mismo
                    if (vecino_f, vecino_c) not in mis_coordenadas:
                        # El vecino DEBE ser agua
                        if matriz[vecino_f][vecino_c] != Pieza.W:
                            return False
        return True

    # --- Función principal que orquesta las validaciones ---

    def validar_restricciones(self, tablero_obj) -> bool:
        """
        Orquesta las validaciones. El orden es importante para eficiencia y
        evitar errores de índices.
        """
        # 1. ¿Estoy dentro del mapa?
        if not self.validar_limites(tablero_obj):
            return False
        
        # 2. ¿Alguien me pisó? (Solapamiento)
        if not self.validar_integridad(tablero_obj):
            return False
            
        # 3. ¿Tengo suficiente espacio alrededor?
        if not self.validar_espaciado(tablero_obj):
            return False
            
        return True

class Barco(Objetivo):
    def __init__(self, ubicacion: tuple[int, int], longitud: int, direccion: Direccion):
        self.longitud = longitud
        self.direccion = direccion
        super().__init__(ubicacion, self.construir_partes_barco(ubicacion))
        
    def construir_partes_barco(self, ubicacion):
        partes = [None] * self.longitud
        f_ini, c_ini = ubicacion
        
        if self.direccion == Direccion.VERTICAL:
            partes[0] = Celda(f_ini, c_ini, Pieza.T)
            partes[-1] = Celda(f_ini + self.longitud - 1, c_ini, Pieza.B)
            for i in range(1, self.longitud - 1):
                partes[i] = Celda(f_ini + i, c_ini, Pieza.M)

        elif self.direccion == Direccion.HORIZONTAL:
            partes[0] = Celda(f_ini, c_ini, Pieza.L)
            partes[-1] = Celda(f_ini, c_ini + self.longitud - 1, Pieza.R)
            for i in range(1, self.longitud - 1):
                partes[i] = Celda(f_ini, c_ini + i, Pieza.M)
        
        return partes

class Submarino(Objetivo):
    def __init__(self, ubicacion: tuple[int,int]):
        super().__init__(ubicacion, [Celda(ubicacion[0], ubicacion[1], Pieza.C)])

class Tablero:
    def __init__(self, nFilas: int, nColumnas: int, 
                 flota: list[Objetivo], 
                 pistas: tuple[int,int,Pieza], 
                 pistas_filas: list[int], 
                 pistas_cols: list[int]):
        
        self.tamano_tablero = (nFilas, nColumnas)
        self.flota = flota
        self.pistas = pistas
        self.pistas_filas = pistas_filas 
        self.pistas_cols = pistas_cols
        self.matriz = self.construir_matriz()

    def construir_matriz(self):
        filas, cols = self.tamano_tablero
        matriz = [[Pieza.W for _ in range(cols)] for _ in range(filas)]

        for obj in self.flota:
            for celda in obj.partes:
                f, c = celda.fila, celda.columna
                # Solo pintamos si está dentro para evitar crash en construcción
                if 0 <= f < filas and 0 <= c < cols:
                    matriz[f][c] = celda.tipo
        return matriz
    
    def validar_cuentas(self) -> bool:
        filas, cols = self.tamano_tablero
        
        # Validar Filas
        for f in range(filas):
            suma_actual = sum(1 for c in range(cols) if self.matriz[f][c].es_barco())
            if suma_actual != self.pistas_filas[f]:
                return False
                
        # Validar Columnas
        for c in range(cols):
            suma_actual = sum(1 for f in range(filas) if self.matriz[f][c].es_barco())
            if suma_actual != self.pistas_cols[c]:
                return False
                
        return True
    
    def validar_pistas(self) -> bool:

        for fila, columna, tipo in self.pistas:
            if self.matriz[fila][columna] != tipo:
                return False
        
        return True
    
    def obtener_barcos_invalidos(self) -> list[Objetivo]:
        return [barco for barco in self.flota if not barco.validar_restricciones(self)]
    