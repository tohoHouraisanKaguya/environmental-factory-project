import bpy, bmesh, math
from mathutils import Vector
TAG="film_geometry"

class MeshBatch:
    def __init__(self): self.v=[]; self.f=[]
    def box(self, center, size):
        x,y,z=center; a,b,c=(q/2 for q in size); k=len(self.v)
        self.v += [(x+dx*a,y+dy*b,z+dz*c) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
        self.f += [tuple(k+i for i in f) for f in [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]]
    def rod(self,a,b,r,n=12):
        a,b=Vector(a),Vector(b); d=b-a
        if d.length < 1e-8: return
        q=d.to_track_quat('Z','Y'); k=len(self.v)
        for p in (a,b):
            self.v += [tuple(p+q@Vector((r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),0))) for i in range(n)]
        self.f += [tuple(k+i for i in reversed(range(n))),tuple(k+n+i for i in range(n))]
        self.f += [(k+i,k+(i+1)%n,k+(i+1)%n+n,k+i+n) for i in range(n)]
    def ring(self,ri,ro,zi,zo,thickness,n=192):
        # Closed annular shell; top inner and outer elevations can differ for floor slope.
        k=len(self.v)
        for r,z in [(ri,zi),(ro,zo),(ri,zi-thickness),(ro,zo-thickness)]:
            self.v += [(r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for i in range(n)]
        for i in range(n):
            j=(i+1)%n
            for f in [(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)]:
                self.f.append(tuple(k+x for x in f))
    def object(self,name,col,mat):
        me=bpy.data.meshes.new(name+'_Mesh'); me.from_pydata(self.v,[],self.f); me.update()
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
        o=bpy.data.objects.new(name,me); col.objects.link(o)
        if mat: me.materials.append(mat)
        o['generator']=TAG
        return o
