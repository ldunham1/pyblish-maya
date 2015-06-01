import pyblish.api

import maya.cmds as cmds


@pyblish.api.log
class SelectObjectSet(pyblish.api.Selector):
    """Identify publishable instances via an associated identifier

    The identifier is located within the Pyblish configuration
    as `pyblish.identifier` and is typically something
    like "publishable".

    Any node of type objectSet containing this attribute will be
    deemed an `Instance` capable of being published. Additionally,
    the objectSet may contain a "family" attribute that will be
    injected into the given instance.

    Prerequisities:
        INSTANCE is of type `objectSet`
        Each INSTANCE MUST contain the attribute `publishable`
        Each INSTANCE MUST contain the attribute `family`

    """

    hosts = ['maya']
    version = (0, 1, 0)

    def process_context(self, context):
        # what about the other prerequisite attr?
        # use recursive to account for namespaces
        # ls, like almost everything else in maya, will return None if nothing valid to return
        objSetList = cmds.ls("*." + pyblish.api.config['identifier'],
                             objectsOnly=True,
                             type='objectSet',
                             recursive=True,
                             long=True) or []
        for objset in objSetList:
            # use split to get the real shortname (not shortest unique name) incl namespaces
            name = objSet.split('|')[-1].split(':')[-1]
            instance = context.create_instance(name=name)
            self.log.info("Adding instance: {0}".format(objset))
            objsetNodeList = cmds.sets(objset, query=True)
            if objsetNodeList:
                # get the nodes longnames for comparison later
                objsetNodeList = cmds.ls(objsetNodeList, long=True)
                for node in objsetNodeList:
                    if cmds.nodeType(node) == 'transform':
                        descendents = cmds.listRelatives(node,
                                                         allDescendents=True,
                                                         fullPath=True) or []
                        for descendent in descendents:
                            # possibility of decendant also being a member of the set
                            if decendant not in objsetNodeList:
                                instance.add(descendent)
    
                    instance.add(node)

            attrs = cmds.listAttr(objset, userDefined=True) or []
            for attr in attrs:
                # compile for efficiency
                attrPath = objset + "." + attr
                # get type for correct get
                attrType = cmds.getAttr(attrPath, typ=True)
                # what about the other prerequisite attr?
                if attr == pyblish.api.config['identifier']:
                    continue

                try:
                    # precompile attr types in a maya lib
                    attributeTypes = {"parent": ["compound",
                                                 "TdataCompound",
                                                 "long2", "long3",
                                                 "short2", "short3",
                                                 "float2", "float3",
                                                 "double2", "double3".
                                                 "spectrum", "reflectance"],
                                      "message": ["message",
                                                  "mesh"]}
                    # check for compound type attrs - parent & children returned in listAttr
                    if attrType in attributeTypes["parent"]:
                        # ignore parent type attrs
                        continue
                    # check for message type attrs (mesh, curve etc)
                    elif attrType in attributeTypes["message"]:
                        # does set_data account for objects?
                        # if not use json(?) and supply an encoding arg to set_data
                        value = cmds.listConnections(attrPath) or []
                    else:
                        value = cmds.getAttr(attrPath)
                except:
                    continue

                instance.set_data(attr, value=value)
