/** -*- mode: c++; c-indent-level: 4; c++-member-init-indent: 8; comment-column: 35; -*-

   -----------------------------------------------------------------------------
   eoSelectMany.h
   (c) Maarten Keijzer, Marc Schoenauer, GeNeura Team, 2000

   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 2 of the License, or (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public
   License along with this library; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

    Contact: todos@geneura.ugr.es, http://geneura.ugr.es
             Marc.Schoenauer@polytechnique.fr
             mkeijzer@dhi.dk
 */
//-----------------------------------------------------------------------------

#ifndef _eoSelectMany_h
#define _eoSelectMany_h


//-----------------------------------------------------------------------------
#include <eoSelect.h>
#include <eoSelectOne.h>
#include <utils/eoHowMany.h>
#include <cmath>
//-----------------------------------------------------------------------------

/** eoSelectMany selects many individuals using eoSelectOne as it's
    mechanism. Therefore eoSelectMany needs an eoSelectOne in its ctor

    It will use an eoHowMnay to determine the number of guys to select,
     and push them to the back of the destination population.

@ingroup Selectors
*/
template<class EOT>
class eoSelectMany : public eoSelect<EOT>
{
 public:
     /// init
     eoSelectMany(eoSelectOne<EOT>& _select,
                    double  _rate, bool _interpret_as_rate = true)
         : select(_select), howMany(_rate, _interpret_as_rate) {}

     // Ctor with eoHowMany
     eoSelectMany(eoSelectOne<EOT>& _select, eoHowMany _howMany)
         : select(_select), howMany(_howMany) {}

     /**
     The implementation repeatidly selects an individual

     @param _source the source population
     @param _dest  the resulting population (size of this population is the number of times eoSelectOne is called. It empties the destination and adds the selection into it)
     */
  virtual void operator()(const eoPop<EOT>& _source, eoPop<EOT>& _dest)
  {
    unsigned target = howMany(_source.size());

    _dest.resize(target);

    select.setup(_source);

    for (size_t i = 0; i < _dest.size(); ++i)
      _dest[i] = select(_source);
  }

private :
  eoSelectOne<EOT>& select;
  eoHowMany howMany;
};

#endif
