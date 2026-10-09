// Independent homogeneous-medium travel-time validation; NOT the Tan et al. workflow.
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
struct Point { double x,y,z; };
struct Pick { Point s; double t; };
struct Fit { Point x; double t0, rms; };
double distance(Point a,Point b) {
    return std::sqrt((a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y)+(a.z-b.z)*(a.z-b.z));
}
double travel(Point x,Point s,double v) { return distance(x,s)/v; }
Fit fit_at(Point x,const std::vector<Pick>& p,double v) {
    double t0=0,ss=0;
    for(auto a:p) t0+=a.t-travel(x,a.s,v);
    t0/=p.size();
    for(auto a:p) { double e=a.t-t0-travel(x,a.s,v); ss+=e*e; }
    return {x,t0,std::sqrt(ss/p.size())};
}
Fit locate(const std::vector<Pick>& p,double v,double h,int levels,
           Point truth,std::ostream* history=nullptr) {
    Fit best{{0,0,0},0,std::numeric_limits<double>::infinity()};
    Point lo{-4000,-4000,0},hi{4000,4000,4000};
    for(int k=0;k<levels;k++) {
        for(double x=lo.x;x<=hi.x+h*1e-6;x+=h)
          for(double y=lo.y;y<=hi.y+h*1e-6;y+=h)
            for(double z=lo.z;z<=hi.z+h*1e-6;z+=h) {
                Fit f=fit_at({x,y,z},p,v);
                if(f.rms<best.rms) best=f;
            }
        if(history) *history<<k<<","<<h<<","<<best.x.x<<","<<best.x.y<<","<<best.x.z
                            <<","<<best.t0<<","<<best.rms<<","<<distance(best.x,truth)<<"\n";
        lo={std::max(-4000.,best.x.x-h),std::max(-4000.,best.x.y-h),std::max(0.,best.x.z-h)};
        hi={std::min(4000.,best.x.x+h),std::min(4000.,best.x.y+h),std::min(4000.,best.x.z+h)};
        h/=2;
    }
    return best;
}
int main(int argc,char** argv) {
 try {
    if(argc!=3) throw std::runtime_error("usage: validation config/validation.txt data");
    std::ifstream cfg(argv[1]); std::string line;
    if(!cfg) throw std::runtime_error("missing configuration");
    while(std::getline(cfg,line) && (line.empty()||line[0]=='#')) {}
    double v,t0,h; Point truth; int levels;
    std::istringstream is(line);
    if(!(is>>v>>truth.x>>truth.y>>truth.z>>t0>>h>>levels) || v<=0 || h<=0 || levels<1 || levels>20)
        throw std::runtime_error("invalid configuration");
    auto output=[&](std::string name) {
        std::ofstream f(std::string(argv[2])+"/"+name); if(!f) throw std::runtime_error("output open failed");
        f<<std::setprecision(16); return f;
    };
    auto checks=output("checks.csv"); checks<<"check,value,tolerance,pass\n";
    bool ok=true;
    auto check=[&](std::string n,double value,double tol) {
        bool pass=std::isfinite(value)&&value<=tol; ok=ok&&pass;
        checks<<n<<","<<value<<","<<tol<<","<<(pass?1:0)<<"\n";
    };
    check("zero_path_s",travel({0,0,0},{0,0,0},v),1e-14);
    check("vertical_path_s",std::abs(travel({0,0,4000},{0,0,0},v)-4000/v),1e-14);
    check("pythagorean_path_s",std::abs(travel({3000,0,4000},{0,0,0},v)-5000/v),1e-14);
    std::vector<Pick> picks;
    auto pf=output("picks.csv"); pf<<"station,x_m,y_m,z_m,arrival_s\n";
    for(int j=0;j<12;j++) {
        double a=2*std::acos(-1.)*j/12,rad=1500+500*(j%4);
        Point s{rad*std::cos(a),rad*std::sin(a),0};
        picks.push_back({s,t0+travel(truth,s,v)});
        pf<<j<<","<<s.x<<","<<s.y<<",0,"<<picks.back().t<<"\n";
    }
    auto history=output("convergence.csv");
    history<<"level,grid_m,x_m,y_m,z_m,t0_s,rms_s,location_error_m\n";
    Fit base=locate(picks,v,h,levels,truth,&history);
    check("exact_location_error_m",distance(base.x,truth),1.0);
    check("exact_origin_error_s",std::abs(base.t0-t0),0.00025);
    check("exact_arrival_rms_s",base.rms,0.0001);
    auto shifted=picks; for(auto& p:shifted) p.t+=17;
    Fit shift=locate(shifted,v,h,levels,truth);
    check("origin_shift_location_m",distance(base.x,shift.x),1e-10);
    check("origin_shift_time_s",std::abs(shift.t0-base.t0-17),1e-12);
    auto reversed=picks; std::reverse(reversed.begin(),reversed.end());
    Fit rev=locate(reversed,v,h,levels,truth);
    check("station_permutation_location_m",distance(base.x,rev.x),1e-10);
    check("depth_reflection_rms_s",fit_at({truth.x,truth.y,-truth.z},picks,v).rms,1e-12);
    auto sensitivity=output("sensitivity.csv");
    sensitivity<<"velocity_ratio,location_error_m,depth_m,rms_s\n";
    for(double ratio:{0.9,0.95,1.0,1.05,1.1}) {
        Fit f=locate(picks,v*ratio,h,levels,truth);
        sensitivity<<ratio<<","<<distance(f.x,truth)<<","<<f.x.z<<","<<f.rms<<"\n";
    }
    auto residuals=output("residuals.csv"); residuals<<"station,arrival_s,predicted_s,residual_s\n";
    for(size_t j=0;j<picks.size();j++) {
        auto p=picks[j]; double pred=base.t0+travel(base.x,p.s,v);
        residuals<<j<<","<<p.t<<","<<pred<<","<<p.t-pred<<"\n";
    }
    std::cout<<"Synthetic validation "<<(ok?"PASS":"FAIL")<<"; location error "
             <<distance(base.x,truth)<<" m; arrival RMS "<<base.rms<<" s\n";
    return ok?0:1;
 } catch(const std::exception& e) { std::cerr<<e.what()<<"\n"; return 2; }
}
