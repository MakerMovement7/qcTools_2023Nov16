<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyMaxScale="1" styleCategories="AllStyleCategories" simplifyLocal="1" readOnly="0" maxScale="0" minScale="1e+08" version="3.10.6-A Coruña" simplifyAlgorithm="0" simplifyDrawingTol="1" labelsEnabled="0" hasScaleBasedVisibilityFlag="0" simplifyDrawingHints="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 symbollevels="0" forceraster="0" enableorderby="0" type="singleSymbol">
    <symbols>
      <symbol clip_to_extent="1" force_rhr="0" name="0" alpha="1" type="marker">
        <layer locked="0" pass="0" enabled="1" class="SimpleMarker">
          <prop k="angle" v="0"/>
          <prop k="color" v="229,182,54,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="35,35,35,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="MM"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option name="name" value="" type="QString"/>
              <Option name="properties"/>
              <Option name="type" value="collection" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer diagramType="Histogram" attributeLegend="1">
    <DiagramCategory diagramOrientation="Up" sizeScale="3x:0,0,0,0,0,0" backgroundAlpha="255" penAlpha="255" penWidth="0" height="15" rotationOffset="270" labelPlacementMethod="XHeight" backgroundColor="#ffffff" enabled="0" lineSizeType="MM" scaleDependency="Area" opacity="1" barWidth="5" sizeType="MM" width="15" minScaleDenominator="0" penColor="#000000" scaleBasedVisibility="0" maxScaleDenominator="1e+08" lineSizeScale="3x:0,0,0,0,0,0" minimumSize="0">
      <fontProperties description="MS Shell Dlg 2,8.25,-1,5,50,0,0,0,0,0" style=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings dist="0" obstacle="0" showAll="1" placement="0" linePlacementFlags="18" priority="0" zIndex="0">
    <properties>
      <Option type="Map">
        <Option name="name" value="" type="QString"/>
        <Option name="properties"/>
        <Option name="type" value="collection" type="QString"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="id">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="false" type="bool"/>
            <Option name="UseHtml" value="false" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="Error">
      <editWidget type="ValueMap">
        <config>
          <Option type="Map">
            <Option name="map" type="List">
              <Option type="Map">
                <Option name="Missing" value="Missing" type="QString"/>
              </Option>
              <Option type="Map">
                <Option name="Presence" value="Presence" type="QString"/>
              </Option>
              <Option type="Map">
                <Option name="Accuracy" value="Accuracy" type="QString"/>
              </Option>
              <Option type="Map">
                <Option name="Type" value="Type" type="QString"/>
              </Option>
              <Option type="Map">
                <Option name="Association" value="Association" type="QString"/>
              </Option>
              <Option type="Map">
                <Option name="Heading" value="Heading" type="QString"/>
              </Option>
            </Option>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="QC Tech">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="false" type="bool"/>
            <Option name="UseHtml" value="false" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="Feature ID">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="false" type="bool"/>
            <Option name="UseHtml" value="false" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="Date">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="false" type="bool"/>
            <Option name="UseHtml" value="false" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="Notes">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option name="IsMultiline" value="false" type="bool"/>
            <Option name="UseHtml" value="false" type="bool"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="BPS_Status">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="BPS_Notes">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="Contnuous?">
      <editWidget type="CheckBox">
        <config>
          <Option type="Map">
            <Option name="CheckedState" value="" type="QString"/>
            <Option name="UncheckedState" value="" type="QString"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="Feature">
      <editWidget type="ValueMap">
        <config>
          <Option type="Map">
            <Option name="map" type="List">
              <Option type="Map">
                <Option name="Boundary" value="Boundary" type="QString"/>
              </Option>
              <Option type="Map">
                <Option name="Delineator" value="Delineator" type="QString"/>
              </Option>
              <Option type="Map">
                <Option name="Path" value="Path" type="QString"/>
              </Option>
              <Option type="Map">
                <Option name="Path Crossings" value="Path Crossings" type="QString"/>
              </Option>
              <Option type="Map">
                <Option name="Road Objects" value="Road Objects" type="QString"/>
              </Option>
              <Option type="Map">
                <Option name="Road Units" value="Road Units" type="QString"/>
              </Option>
            </Option>
          </Option>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="id" name="" index="0"/>
    <alias field="Error" name="" index="1"/>
    <alias field="QC Tech" name="" index="2"/>
    <alias field="Feature ID" name="" index="3"/>
    <alias field="Date" name="" index="4"/>
    <alias field="Notes" name="" index="5"/>
    <alias field="BPS_Status" name="" index="6"/>
    <alias field="BPS_Notes" name="" index="7"/>
    <alias field="Contnuous?" name="" index="8"/>
    <alias field="Feature" name="" index="9"/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default expression="" applyOnUpdate="0" field="id"/>
    <default expression="" applyOnUpdate="0" field="Error"/>
    <default expression="" applyOnUpdate="0" field="QC Tech"/>
    <default expression="" applyOnUpdate="0" field="Feature ID"/>
    <default expression="" applyOnUpdate="0" field="Date"/>
    <default expression="" applyOnUpdate="0" field="Notes"/>
    <default expression="" applyOnUpdate="0" field="BPS_Status"/>
    <default expression="" applyOnUpdate="0" field="BPS_Notes"/>
    <default expression="" applyOnUpdate="0" field="Contnuous?"/>
    <default expression="" applyOnUpdate="0" field="Feature"/>
  </defaults>
  <constraints>
    <constraint constraints="0" field="id" unique_strength="0" notnull_strength="0" exp_strength="0"/>
    <constraint constraints="0" field="Error" unique_strength="0" notnull_strength="0" exp_strength="0"/>
    <constraint constraints="0" field="QC Tech" unique_strength="0" notnull_strength="0" exp_strength="0"/>
    <constraint constraints="0" field="Feature ID" unique_strength="0" notnull_strength="0" exp_strength="0"/>
    <constraint constraints="0" field="Date" unique_strength="0" notnull_strength="0" exp_strength="0"/>
    <constraint constraints="0" field="Notes" unique_strength="0" notnull_strength="0" exp_strength="0"/>
    <constraint constraints="0" field="BPS_Status" unique_strength="0" notnull_strength="0" exp_strength="0"/>
    <constraint constraints="0" field="BPS_Notes" unique_strength="0" notnull_strength="0" exp_strength="0"/>
    <constraint constraints="0" field="Contnuous?" unique_strength="0" notnull_strength="0" exp_strength="0"/>
    <constraint constraints="0" field="Feature" unique_strength="0" notnull_strength="0" exp_strength="0"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" field="id" desc=""/>
    <constraint exp="" field="Error" desc=""/>
    <constraint exp="" field="QC Tech" desc=""/>
    <constraint exp="" field="Feature ID" desc=""/>
    <constraint exp="" field="Date" desc=""/>
    <constraint exp="" field="Notes" desc=""/>
    <constraint exp="" field="BPS_Status" desc=""/>
    <constraint exp="" field="BPS_Notes" desc=""/>
    <constraint exp="" field="Contnuous?" desc=""/>
    <constraint exp="" field="Feature" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction key="Canvas" value="{00000000-0000-0000-0000-000000000000}"/>
  </attributeactions>
  <attributetableconfig sortExpression="" actionWidgetStyle="dropDown" sortOrder="0">
    <columns>
      <column width="-1" name="id" type="field" hidden="0"/>
      <column width="-1" name="Error" type="field" hidden="0"/>
      <column width="-1" name="QC Tech" type="field" hidden="0"/>
      <column width="-1" name="Feature ID" type="field" hidden="0"/>
      <column width="-1" name="Date" type="field" hidden="0"/>
      <column width="-1" name="Notes" type="field" hidden="0"/>
      <column width="-1" name="BPS_Status" type="field" hidden="0"/>
      <column width="-1" name="BPS_Notes" type="field" hidden="0"/>
      <column width="-1" name="Contnuous?" type="field" hidden="0"/>
      <column width="-1" type="actions" hidden="1"/>
      <column width="-1" name="Feature" type="field" hidden="0"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <storedexpressions/>
  <editform tolerant="1">C:/Users/jgreener/Desktop/New folder/QT_Designer_Custom_Form_Template.ui</editform>
  <editforminit>formOpen</editforminit>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath>C:\Users\jgreener\Desktop\New folder\RFDB_USHR QC_BPS_FeedbackForm.py</editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field editable="1" name="BPS_Notes"/>
    <field editable="1" name="BPS_Status"/>
    <field editable="1" name="Contnuous?"/>
    <field editable="1" name="Date"/>
    <field editable="1" name="Error"/>
    <field editable="1" name="Feature"/>
    <field editable="0" name="Feature ID"/>
    <field editable="1" name="Notes"/>
    <field editable="0" name="QC Tech"/>
    <field editable="1" name="Status"/>
    <field editable="0" name="id"/>
  </editable>
  <labelOnTop>
    <field name="BPS_Notes" labelOnTop="0"/>
    <field name="BPS_Status" labelOnTop="0"/>
    <field name="Contnuous?" labelOnTop="0"/>
    <field name="Date" labelOnTop="0"/>
    <field name="Error" labelOnTop="0"/>
    <field name="Feature" labelOnTop="0"/>
    <field name="Feature ID" labelOnTop="0"/>
    <field name="Notes" labelOnTop="0"/>
    <field name="QC Tech" labelOnTop="0"/>
    <field name="Status" labelOnTop="0"/>
    <field name="id" labelOnTop="0"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>id</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>0</layerGeometryType>
</qgis>
