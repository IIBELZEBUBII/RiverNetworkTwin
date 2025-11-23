from qgis.core import QgsProject, QgsField, QgsWkbTypes, QgsWkbType, QgsExpression
from qgis.PyQt.QtCore import QVariant


def calculate_geometry_stats(layer_name):

    # 1. Получение активного слоя по имени
    layer = QgsProject.instance().mapLayersByName(layer_name)
    if not layer:
        print(f"Ошибка: Слой с именем '{layer_name}' не найден.")
        return

    layer = layer[0]

    if layer.geometryType() != QgsWkbTypes.Polygon:
        print("Ошибка: Слой должен быть полигональным (Polygon).")
        return

    print(f"Начало обработки слоя: {layer.name()}")

    # 2. Подготовка и добавление новых полей
    area_field_name = 'Area_SqM'
    length_field_name = 'Length_M'

    fields = layer.fields()

    if not fields.indexOf(area_field_name) != -1:
        layer.startEditing()
        layer.addAttribute(QgsField(area_field_name, QVariant.Double, 'double', 15, 3))
        layer.commitChanges()
        print(f"Добавлено поле: {area_field_name}")

    if not fields.indexOf(length_field_name) != -1:
        layer.startEditing()
        layer.addAttribute(QgsField(length_field_name, QVariant.Double, 'double', 15, 3))
        layer.commitChanges()
        print(f"Добавлено поле: {length_field_name}")


    fields = layer.fields()
    area_index = fields.indexOf(area_field_name)
    length_index = fields.indexOf(length_field_name)

    # 3. Расчет значений и обновление атрибутов

    layer.startEditing()

    feature_count = 0

    for feature in layer.getFeatures():
        geom = feature.geometry()


        area = geom.area()


        length = geom.length()


        feature[area_index] = area
        feature[length_index] = length


        layer.updateFeature(feature)
        feature_count += 1

    # 4. Завершение сессии редактирования и вывод результата
    layer.commitChanges()

    print(f"\nУспешно обновлено {feature_count} объектов.")
    print("Расчет площади и периметра завершен.")


# --- Пример использования ---

#layer_name_to_process = 'Hydrographic_Zones'
#calculate_geometry_stats(layer_name_to_process)